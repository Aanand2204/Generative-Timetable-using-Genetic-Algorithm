document.getElementById("timetableForm").addEventListener("submit", function(event) {
    event.preventDefault();

    let formData = new FormData(this);

    // Collect subject credits from user input
    let creditData = {};
    document.querySelectorAll(".credit-input").forEach(input => {
        creditData[input.name] = input.value;
    });

    formData.append("credits", JSON.stringify(creditData));

    fetch("/generate", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        let tableBody = document.querySelector("#timetable tbody");
        tableBody.innerHTML = "";

        if (data.error) {
            alert("Error: " + data.error);
            return;
        }

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
    .catch(error => console.error("Error fetching timetable:", error));
});

// Fetch subjects when class and semester are entered
document.getElementById("semester").addEventListener("change", function() {
    let className = document.getElementById("class_name").value;
    let semester = document.getElementById("semester").value;

    if (className && semester) {
        fetch(`/subjects?class_name=${className}&semester=${semester}`)
        .then(response => response.json())
        .then(subjects => {
            let creditInputsDiv = document.getElementById("creditInputs");
            creditInputsDiv.innerHTML = "<h3>Enter Credits for Each Subject</h3>";

            subjects.forEach(subject => {
                let inputField = `<label>${subject}:</label>
                                  <input type="number" name="${subject}" class="credit-input" min="1" required><br>`;
                creditInputsDiv.innerHTML += inputField;
            });
        });
    }
});
