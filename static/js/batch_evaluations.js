/**
 * Parses a progress string from the batch evaluation stream.
 * @param {string} progressStr - The progress string to parse.
 * @returns {object|null} An object with parsed progress fields, or null if parsing fails.
 */
function parseProgress(progressStr) {
  // Format: Eval x/y - Model: ... Subject: ... Exam: ... Repetition: a/b
  const progressRegex = /^Eval (\d+)\/(\d+) - Model: (.*?) Subject: (.*?) Exam: (.*?) Repetition: (\d+)\/(\d+)$/;
  const match = progressStr.match(progressRegex);
  if (!match) return null;
  return {
    currentEval: parseInt(match[1], 10),
    totalEval: parseInt(match[2], 10),
    model: match[3],
    subject: match[4],
    exam: match[5],
    repetition: match[6],
    totalReps: match[7],
    evalMsg: `Eval ${match[1]}/${match[2]}`,
    detailMsg: `Evaluating ${match[3]} on ${match[4]} with ${match[5]} (${match[6]}/${match[7]})`
  };
}

/**
 * Updates the progress bar UI with the current evaluation progress.
 * @param {object} progress - The progress object returned by parseProgress.
 */
function updateProgressBar(progress) {
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
    .text(progress.evalMsg);
  if (!isNaN(progress.currentEval) && !isNaN(progress.totalEval) && progress.totalEval > 0) {
    const percent = Math.round((progress.currentEval / progress.totalEval) * 100);
    $("#progress-bar").css("width", percent + "%");
  }
}

/**
 * Collects and prepares form data from the batch evaluation form as a JSON object.
 * @param {HTMLFormElement} formElem - The form element to collect data from.
 * @returns {object} The form data as a plain object suitable for JSON serialization.
 */
function collectBatchEvalFormData(formElem) {
  const formData = new FormData(formElem);
  const data = {};
  formData.forEach((value, key) => {
    if (key.endsWith('[]')) {
      if (!data[key]) data[key] = [];
      data[key].push(value);
    } else {
      data[key] = value;
    }
  });
  return data;
}

/**
 * Handles the streaming response from the batch evaluation POST request.
 * Reads and processes each chunk of streamed data.
 * @param {Response} response - The fetch response object.
 * @returns {Promise<void>} Resolves when the stream is fully processed.
 */
function handleBatchEvalStream(response) {
  if (!response.ok) {
    $("#loading-indicator").hide();
    $("#batch-eval-results").html("Error starting batch evaluation.");
    throw new Error("Network response was not ok");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = '';
  function processStream({ done, value }) {
    if (done) {
      $("#loading-indicator").hide();
      return;
    }
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || '';
    chunks.forEach(chunk => processBatchEvalChunk(chunk));
    return reader.read().then(processStream);
  }
  return reader.read().then(processStream);
}

/**
 * Processes a single chunk of streamed data from the batch evaluation.
 * Updates the UI based on the type of message received.
 * @param {string} chunk - The chunk of data to process.
 */
function processBatchEvalChunk(chunk) {
  if (chunk.trim() === "") return;
  try {
    const data = JSON.parse(chunk.replace("data: ", ""));
    if (data.error) {
      $("#batch-eval-results").append(`<div style='color:red;'>${data.error}</div>`);
    } else if (data.progress) {
      const progress = parseProgress(data.progress);
      if (progress) {
        window._batchEvalLastRow = {
          model: progress.model,
          subject: progress.subject,
          exam: progress.exam,
          repetition: progress.repetition,
        };
        updateProgressBar(progress);
        $("#batch-eval-results").html(`<div style='font-size:1.1em;margin-top:0.5em;'>${progress.detailMsg}</div>`);
      } else {
        $("#progress-bar").text(data.progress);
      }
    } else if (data.processed_questions && data.response) {
      // Show per-question result as it arrives
      const response = data.response;
      const responseColor = response.is_correct ? "green" : "red";
      const detailsHtml = `
        <div style="border:1px solid #ccc; padding:8px; margin:8px 0; border-radius:4px;">
          <b>Question ${data.processed_questions}:</b>
          <pre>${response.question_prompt}</pre>
          <b>Model response:</b> <span style="color:${responseColor}; font-weight:bold;">${response.response}</span><br>
          <b>Correct option:</b> ${response.correct_option}
          <span style="margin-left:1em;">${response.is_correct ? "✅" : "❌"}</span>
          <div style="font-size:0.9em; color:#888;">Time: ${data.time || "-"}s</div>
        </div>
      `;
      $("#exam-details").append(detailsHtml);
    } else if (data.response) {
      // Use appendResponseDetails from utils.js for consistent UI
      const progressLike = {
        response: data.response,
        time: data.response.time || '-',
        processed_questions: data.response.processed_questions || '-',
        total_questions: data.response.total_questions || '-',
      };
      appendResponseDetails(progressLike);
    } else if (data.processed_questions && data.total_questions) {
      const percent = Math.round((data.processed_questions / data.total_questions) * 100);
      $("#progress-bar").css("width", percent + "%");
    } else if (data.eval_result) {
      // Show the result of the last eval (grade and time)
      const grade = data.eval_result.grade;
      const time = data.eval_result.time;
      // Find or create a summary area
      let $summary = $("#batch-eval-summary");
      if ($summary.length === 0) {
        $summary = $("<div id='batch-eval-summary' class='batch-eval-summary'></div>");
        $("#batch-eval-results").append($summary);
      }
      $summary.html(
        `Result: <b>${grade}</b> correct, Time: <b>${time}s</b>`
      );
      // Move the summary above the details, but below the progress message
      $("#batch-eval-summary").insertAfter("#batch-eval-results > div:first-child");
      // --- Add row to table ---
      const lastRow = window._batchEvalLastRow || {};
      $("#batch-eval-table").show();
      $("#batch-eval-table tbody").append(
        `<tr>
          <td data-label="Model">${lastRow.model||''}</td>
          <td data-label="Subject">${lastRow.subject||''}</td>
          <td data-label="Exam">${lastRow.exam||''}</td>
          <td data-label="Repetition">${lastRow.repetition||''}</td>
          <td data-label="Grade">${grade}</td>
          <td data-label="Time">${time}</td>
        </tr>`
      );
    } else if (data.done) {
      // Do not clear or append, just mark finished
      $("#batch-eval-results").html("<div>Batch evaluation finished.</div>");
      $("#loading-indicator").hide();
    }
  } catch (e) {
    console.error("Error parsing chunk:", e);
  }
}

$(document).ready(function () {
  $("#batch-eval-form").submit(function (event) {
    event.preventDefault(); // Prevent default form submission

    // UI: Reset state
    $("#loading-indicator").show();
    $("#progress-bar").css("width", "0%").text("0%");
    $("#batch-eval-results").html("");
    $("#exam-details").html("");
    
    // Collect and prepare data
    const data = collectBatchEvalFormData(this);
    
    // Fetch and handle stream
    fetch(window.location.pathname, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val(),
      },
      body: JSON.stringify(data),
    })
      .then(handleBatchEvalStream)
      .catch((error) => {
        $("#loading-indicator").hide();
        $("#batch-eval-results").html("Error: " + error.message);
      });
  });
});

/**
 * Updates the evaluation count indicator based on selected exams, models, and repetitions.
 */
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
