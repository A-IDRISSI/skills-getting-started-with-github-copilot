import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from copy import deepcopy

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.app import activities, app


HARNESS = """
<!doctype html>
<pre id="result">PENDING</pre>
<iframe src="/static/index.html"></iframe>
<script>
const frame = document.querySelector("iframe");
const waitFor = async (check) => {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  throw new Error("Timed out waiting for the activity card to update");
};
frame.addEventListener("load", async () => {
  try {
    const doc = frame.contentDocument;
    const email = "signup-refresh-test@mergington.edu";
    await waitFor(() => doc.querySelector(".activity-card"));
    const card = () => [...doc.querySelectorAll(".activity-card")]
      .find(element => element.querySelector("h4").textContent === "Art Club");
    const signUp = async () => {
      doc.getElementById("email").value = email;
      doc.getElementById("activity").value = "Art Club";
      doc.getElementById("signup-form").requestSubmit();
      await waitFor(() => card().textContent.includes(email));
      if (!card().textContent.includes("17 spots left")) throw new Error("Stale availability");
      if (card().querySelector("h5").textContent !== "Participants (1)") {
        throw new Error("Stale participant count");
      }
      if (doc.getElementById("activity").options.length !== 10) {
        throw new Error("Duplicate activity options");
      }
      if (doc !== frame.contentDocument) throw new Error("Page was reloaded");
    };
    await signUp();
    card().querySelector(".delete-participant").click();
    await waitFor(() => card().querySelector(".participants-empty"));
    await signUp();
    document.getElementById("result").textContent = "PASS";
  } catch (error) {
    document.getElementById("result").textContent = "FAIL: " + error.message;
  }
});
</script>
"""


@unittest.skipUnless(shutil.which("google-chrome"), "Google Chrome is required")
class SignupUITests(unittest.TestCase):
    def test_signup_updates_card_without_page_reload(self):
        original = deepcopy(activities)
        self.addCleanup(self.restore_activities, original)
        test_app = FastAPI()

        @test_app.get("/__test", response_class=HTMLResponse)
        def harness():
            return HARNESS

        test_app.mount("/", app)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(test_app, log_level="error"))
            thread = threading.Thread(
                target=server.run, kwargs={"sockets": [listener]}, daemon=True
            )
            thread.start()
            try:
                deadline = time.monotonic() + 5
                while not server.started and thread.is_alive() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(server.started, "Test server failed to start")
                with tempfile.TemporaryDirectory(prefix="signup-browser-") as profile:
                    result = subprocess.run(
                        [
                            shutil.which("google-chrome"),
                            "--headless",
                            "--disable-gpu",
                            f"--user-data-dir={profile}",
                            "--virtual-time-budget=10000",
                            "--dump-dom",
                            f"http://127.0.0.1:{port}/__test",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('<pre id="result">PASS</pre>', result.stdout)
            finally:
                server.should_exit = True
                thread.join(timeout=5)

    @staticmethod
    def restore_activities(original):
        activities.clear()
        activities.update(original)
