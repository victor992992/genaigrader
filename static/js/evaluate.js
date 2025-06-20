$(document).ready(function () {
  function toggleCourseInputs() {
    const courseChoice = $('input[name="course_choice"]:checked').val();
    if (courseChoice === 'new') {
      $('#course-select').hide();
      $('#new-course-input').show().prop('required', true);
    } else {
      $('#course-select').show();
      $('#new-course-input').hide().prop('required', false);
    }
  }

  toggleCourseInputs();
  $('input[name="course_choice"]').change(toggleCourseInputs);

  $("#exam-form").submit(function (event) {
    event.preventDefault();

    const courseChoice = $('input[name="course_choice"]:checked').val();
    if (courseChoice === 'new' && !$('#new-course-input').val().trim()) {
      alert('Please enter the name of the new course');
      return;
    }

    resetUI();
    const formData = new FormData(this);

    fetch("/upload/", {
      method: "POST",
      body: formData,
      headers: { "Cache-Control": "no-cache" },
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
        $("#exam-results").html("Error processing the file.");
      });
  });
});
