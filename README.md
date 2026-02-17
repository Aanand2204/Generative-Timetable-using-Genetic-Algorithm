# Generative Timetable using Genetic Algorithm

An automated system to generate optimized college/university timetables using Artificial Intelligence (Genetic Algorithm). This project ensures no scheduling conflicts, respects subject priorities, and optimizes resource allocation.

## 🚀 Getting Started

Follow these steps to set up the project on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/Aanand2204/Generative-Timetable-using-Genetic-Algorithm.git
cd Generative-Timetable-using-Genetic-Algorithm
```

### 2. Prerequisites
- Python 3.8+
- MySQL Server

### 3. Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Variables (.env)
The application requires several environment variables for database connectivity and security.
- Create a file named `.env` in the root directory.
- Use `.env.example` as a template.
- **Note:** Ensure you configure your database credentials correctly in this file.

Example `.env` content:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=timetabledb
DB_PORT=3306
SECRET_KEY=your_random_secret_key
```

### 6. Database Setup
1. Open your MySQL client (e.g., MySQL Workbench or Command Line).
2. Create a database named `timetabledb`.
3. Import the database schema from `schema.sql`:
   ```bash
   mysql -u root -p timetabledb < schema.sql
   ```

### 7. Run the Application
```bash
python app.py
```
After running, the server should be available at `http://127.0.0.1:5000`.

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Algorithm:** Genetic Algorithm
- **Database:** MySQL
- **Frontend:** HTML/CSS/JavaScript (located in `templates/` and `static/`)

