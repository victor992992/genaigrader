$(document).ready(function () {
  $("#reevaluate-form").submit(function (event) {
    event.preventDefault();

    const examId = $("#exam-select").val();
    const model = $("#model-select").val();
    const userPrompt = $("#user-prompt").val();

    if (!examId) {
      alert("Please select an exam");
      return;
    }

    resetUI();

    const payload = {
      exam_id: examId,
      model: model,
      user_prompt: userPrompt,
    };

    fetch("/reevaluate/process/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        if (!response.ok) {
          return handleErrorResponse(response, "There was an error processing the file.");
        }
        return handleStreamingResponse(response, updateUI);
      })
      .catch((error) => {
        console.error("Error:", error);
        $("#loading-indicator").hide();
        $("#exam-results").html("Error reevaluating the exam.");
      });
  });
});