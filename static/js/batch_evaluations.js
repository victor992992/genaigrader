// static/js/batch_evaluations.js
$(document).ready(function () {
  $("#batch-eval-form").submit(function (event) {
    event.preventDefault();

    // Collect form data
    const formData = new FormData(this);
    $("#loading-indicator").show();
    $("#progress-bar").css("width", "0%").text("0%");
    $("#batch-eval-results").html("");
    $("#batch-eval-details").html("");

    // Prepare POST request (not using fetch FormData directly for streaming)
    const data = {};
    formData.forEach((value, key) => {
      if (key.endsWith('[]')) {
        if (!data[key]) data[key] = [];
        data[key].push(value);
      } else {
        data[key] = value;
      }
    });

    fetch(window.location.pathname, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val(),
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (!response.ok) {
          $("#loading-indicator").hide();
          $("#batch-eval-results").html("Error starting batch evaluation.");
          throw new Error("Network response was not ok");
        }
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = '';
        let lastProgress = 0;
        let lastExamMsg = '';
        let lastQuestionMsg = '';
        let lastProgressMsg = '';
        let lastEvalMsg = '';
        let lastDetailMsg = '';
        function processStream({ done, value }) {
          if (done) {
            $("#loading-indicator").hide();
            return;
          }
          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split("\n\n");
          buffer = chunks.pop() || '';
          chunks.forEach(chunk => {
            if (chunk.trim() === "") return;
            try {
              const data = JSON.parse(chunk.replace("data: ", ""));
              if (data.error) {
                $("#batch-eval-results").append(`<div style='color:red;'>${data.error}</div>`);
              } else if (data.progress) {
                // Split progress message: Eval x/y - ...
                const match = data.progress.match(/^(Eval (\d+)\/(\d+))( - .*)?$/);
                if (match) {
                  lastEvalMsg = match[1];
                  lastDetailMsg = match[4] ? match[4].trim() : '';
                  // Set progress bar text and background color for visibility
                  $("#progress-bar")
                    .css({
                      'text-align': 'center',
                      'white-space': 'nowrap',
                      'overflow': 'hidden',
                      'text-overflow': 'ellipsis',
                      'font-weight': 'bold',
                      'font-size': '1.1em',
                      'background-color': '#4caf50',
                      'color': 'white',
                      'display': 'flex',
                      'align-items': 'center',
                      'justify-content': 'center',
                      'min-width': '60px',
                      'min-height': '24px',
                    })
                    .text(lastEvalMsg || ' ');
                  // Update progress bar width based on eval count/total
                  const currentEval = parseInt(match[2], 10);
                  const totalEval = parseInt(match[3], 10);
                  if (!isNaN(currentEval) && !isNaN(totalEval) && totalEval > 0) {
                    const percent = Math.round((currentEval / totalEval) * 100);
                    $("#progress-bar").css("width", percent + "%");
                  }
                  $("#batch-eval-results").html(`<div style='font-size:1.1em;margin-top:0.5em;'>${lastDetailMsg}</div>`);
                } else {
                  $("#progress-bar").text(data.progress);
                }
              } else if (data.response) {
                $("#batch-eval-details").append(`<div><b>Q:</b> ${data.response.question_prompt}<br><b>Model:</b> ${data.response.response}</div>`);
              } else if (data.processed_questions && data.total_questions) {
                const percent = Math.round((data.processed_questions / data.total_questions) * 100);
                $("#progress-bar").css("width", percent + "%");
              } else if (data.done) {
                $("#batch-eval-results").append("<div>Batch evaluation finished.</div>");
                $("#loading-indicator").hide();
              }
            } catch (e) {
              console.error("Error parsing chunk:", e);
            }
          });
          return reader.read().then(processStream);
        }
        return reader.read().then(processStream);
      })
      .catch((error) => {
        $("#loading-indicator").hide();
        $("#batch-eval-results").html("Error: " + error.message);
      });
  });
});

// --- Eval count indicator logic ---
function updateEvalCountIndicator() {
  const exams = document.getElementById('exams');
  const models = document.getElementById('models');
  const reps = document.getElementById('repetitions');
  const nExams = exams ? Array.from(exams.selectedOptions).length : 0;
  const nModels = models ? Array.from(models.selectedOptions).length : 0;
  const nReps = reps ? parseInt(reps.value) : 0;
  let total = nExams * nModels * nReps;
  let msg = '';
  if (nExams && nModels && nReps) {
    msg = `Total evaluations to run: <b>${total}</b> (${nExams} exam${nExams>1?'s':''} × ${nModels} model${nModels>1?'s':''} × ${nReps} repetition${nReps>1?'s':''})`;
  } else {
    msg = 'Select at least one exam, one model, and set repetitions.';
  }
  document.getElementById('eval-count-indicator').innerHTML = msg;
}

document.addEventListener('DOMContentLoaded', function() {
  updateEvalCountIndicator();
  document.getElementById('exams').addEventListener('change', updateEvalCountIndicator);
  document.getElementById('models').addEventListener('change', updateEvalCountIndicator);
  document.getElementById('repetitions').addEventListener('input', updateEvalCountIndicator);
});
