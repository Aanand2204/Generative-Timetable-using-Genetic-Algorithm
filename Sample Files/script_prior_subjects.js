document.getElementById("semester").addEventListener("change", function() {
    let className = document.getElementById("class_name").value.trim();
    let semester = document.getElementById("semester").value.trim();

    if (className && semester) {
        fetch(`/subjects?class_name=${className}&semester=${semester}`)
        .then(response => response.json())
        .then(subjects => {
            let creditInputsDiv = document.getElementById("creditInputs");
            creditInputsDiv.innerHTML = "<h3>Enter Credits and Priority for Each Subject</h3>";

            subjects.forEach(subject => {
                let inputField = `
                    <label>${subject} (Priority 1 = Highest, ${subjects.length} = Lowest):</label>
                    <input type="number" name="${subject}" class="credit-input" min="1" required>
                    <input type="number" name="${subject}-priority" class="priority-input" min="1" max="${subjects.length}" required>
                    <br>`;
                creditInputsDiv.innerHTML += inputField;
            });
        })
        .catch(error => alert("⚠️ Failed to fetch subjects."));
    }
});

document.getElementById("timetableForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let formData = new FormData(this);
    let creditData = {};
    let priorityData = {};
    let prioritySet = new Set();
    let totalSubjects = document.querySelectorAll(".priority-input").length;

    document.querySelectorAll(".credit-input").forEach(input => {
        let subjectName = input.name.trim();
        let creditValue = parseInt(input.value, 10);
        creditData[subjectName] = creditValue;
    });

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

    formData.append("credits", JSON.stringify(creditData));
    formData.append("priorities", JSON.stringify(priorityData));

    fetch("/generate", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        let tableBody = document.querySelector("#timetable tbody");
        tableBody.innerHTML = "";

        data.forEach(row => {
            let tr = document.createElement("tr");

            let timeslotTd = document.createElement("td");
            timeslotTd.textContent = row["Timeslot"];
            tr.appendChild(timeslotTd);

            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].forEach(day => {
                let td = document.createElement("td");
                td.textContent = row[day] || "-";
                tr.appendChild(td);
            });

            tableBody.appendChild(tr);
        });
    })
    .catch(error => alert("⚠️ Failed to generate timetable."));
});
