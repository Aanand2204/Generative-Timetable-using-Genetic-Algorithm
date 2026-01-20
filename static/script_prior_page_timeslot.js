document.getElementById("semester").addEventListener("change", function () {
    let className = document.getElementById("class_name").value.trim();
    let semester = document.getElementById("semester").value.trim();

    if (className && semester) {
        fetch(`/subjects?class_name=${className}&semester=${semester}`)
            .then(response => response.json())
            .then(subjects => {
                let priorityInputsDiv = document.getElementById("priorityInputs");
                priorityInputsDiv.innerHTML = "<h3>Enter Priority for Each Subject</h3>";

                subjects.forEach(subject => {
                    let inputField = `
                    <div style="margin-bottom: 1rem;">
                        <label style="display:block; margin-bottom: 0.5rem;">${subject}:</label>
                        <input type="number" name="${subject}-priority" class="priority-input" min="1" max="${subjects.length}" required>
                    </div>`;
                    priorityInputsDiv.innerHTML += inputField;
                });

                priorityInputsDiv.innerHTML += `<p>📌 Each subject must have a unique priority between 1 and ${subjects.length}.</p>`;
            })
            .catch(error => alert("⚠️ Failed to fetch subjects."));
    }
});

document.getElementById("priorityForm").addEventListener("submit", function (event) {
    event.preventDefault();

    let className = document.getElementById("class_name").value.trim();
    let semester = document.getElementById("semester").value.trim();

    if (!className || !semester) {
        alert("⚠️ Class name and semester are required!");
        return;
    }

    let priorityData = {};
    let prioritySet = new Set();
    let totalSubjects = document.querySelectorAll(".priority-input").length;

    document.querySelectorAll(".priority-input").forEach(input => {
        let subjectName = input.name.replace("-priority", "").trim();
        let priorityValue = parseInt(input.value, 10);

        if (isNaN(priorityValue) || priorityValue < 1 || priorityValue > totalSubjects) {
            alert(`⚠️ Please enter a unique priority between 1 and ${totalSubjects} for ${subjectName}.`);
            return;
        }

        if (prioritySet.has(priorityValue)) {
            alert(`⚠️ Priority ${priorityValue} is already assigned. Each subject must have a unique priority.`);
            return;
        }

        prioritySet.add(priorityValue);
        priorityData[subjectName] = priorityValue;
    });

    if (prioritySet.size !== totalSubjects) {
        alert(`⚠️ Each subject must have a **unique** priority from 1 to ${totalSubjects}.`);
        return;
    }

    let startTime = document.getElementById("start_time").value;
    let endTime = document.getElementById("end_time").value;
    let lectureDuration = document.getElementById("lecture_duration").value;
    let breakStart = document.getElementById("break_start").value;
    let breakDuration = document.getElementById("break_duration").value;

    if (!startTime || !endTime || !lectureDuration) {
        alert("⚠️ Please fill in all time configuration fields.");
        return;
    }

    sessionStorage.setItem("class_name", className);
    sessionStorage.setItem("semester", semester);

    fetch("/save_priorities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            class_name: className,
            semester: semester,
            priorities: priorityData,
            time_config: {  // Send new Time Config
                start_time: startTime,
                end_time: endTime,
                lecture_duration: lectureDuration,
                break_start: breakStart,
                break_duration: breakDuration
            }
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = "/credits";
            } else {
                alert("⚠️ Failed to save priorities.");
            }
        })
        .catch(error => alert("⚠️ Error occurred."));
});

