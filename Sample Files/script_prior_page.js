document.getElementById("semester").addEventListener("change", function() {
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
                    <label>${subject}:</label>
                    <input type="number" name="${subject}-priority" class="priority-input" min="1" max="${subjects.length}" required>
                    <br>`;
                priorityInputsDiv.innerHTML += inputField;
            });

            priorityInputsDiv.innerHTML += `<p>📌 Priorities must be unique and range from 1 (Highest) to ${subjects.length} (Lowest).</p>`;
        })
        .catch(error => alert("⚠️ Failed to fetch subjects."));
    }
});

document.getElementById("priorityForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let formData = new FormData(this);
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
        alert(`⚠️ You must assign all priorities uniquely from 1 to ${totalSubjects}.`);
        return;
    }

    fetch("/save_priorities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ class_name: document.getElementById("class_name").value, semester: document.getElementById("semester").value, priorities: priorityData })
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
