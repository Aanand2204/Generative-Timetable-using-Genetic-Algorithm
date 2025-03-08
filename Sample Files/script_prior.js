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
                    <label>${subject} (Priority: 1=High, 2=Medium, 3=Low):</label>
                    <input type="number" name="${subject}" class="credit-input" min="1" required>
                    <select name="${subject}-priority" class="priority-input">
                        <option value="1">1 (High)</option>
                        <option value="2">2 (Medium)</option>
                        <option value="3">3 (Low)</option>
                    </select>
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

    document.querySelectorAll(".credit-input").forEach(input => {
        let subjectName = input.name.trim();
        let creditValue = parseInt(input.value, 10);
        creditData[subjectName] = creditValue;
    });

    document.querySelectorAll(".priority-input").forEach(input => {
        let subjectName = input.name.replace("-priority", "").trim();
        let priorityValue = parseInt(input.value, 10);
        priorityData[subjectName] = priorityValue;
    });

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
