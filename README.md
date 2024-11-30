<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://imgbb.com/"><img src="https://i.ibb.co/W3GcTt9/6291766329023248332-1.jpg" alt="6291766329023248332-1" border="0" width='80' height='80'>
  </a>

<h3 align="center">AUTOLOCK: A WEB-BASED AUTOMATIC ATTENDANCE SYSTEM INTEGRATING RFID SMART DOOR LOCK WITH TOTP ALGORITHM FOR LEARNING LABORATORY</h3>
</div>
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

The AUTOLOCK: A Web-Based Automatic Attendance System Integrating RFID Smart Door Lock with TOTP Algorithm for Learning Laboratory is a capstone project designed to modernize attendance tracking and enhance security in educational laboratory settings. This system integrates cutting-edge technologies, including an Arduino Mega, Flask web framework, and MySQL database, to provide an efficient, reliable, and secure solution for managing access and attendance.

The project leverages RFID (Radio-Frequency Identification) technology to enable seamless student authentication and door access control. Each student uses an RFID card to log their attendance, which is automatically recorded in a centralized database. The system also incorporates the TOTP (Time-Based One-Time Password) algorithm for an additional layer of authentication, ensuring secure faculty access and management capabilities.

Key features of the system include real-time attendance monitoring, automated record-keeping, schedule-based access restrictions, and detailed reporting. The web-based interface allows administrators to manage student schedules, faculty access, and attendance logs efficiently. By integrating hardware and software components, the project delivers a robust and user-friendly solution tailored to the needs of learning laboratories.

The AUTOLOCK system not only streamlines attendance processes but also enhances laboratory security, making it a valuable tool for educational institutions aiming to adopt modern and secure technology solutions.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With
* [![Flask](https://img.shields.io/badge/flask-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/en/stable/)
* [![MySQL](https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=black&logoSize=auto)](https://www.mysql.com/)
* [![SQLALCHEMY](https://img.shields.io/badge/sqlalchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=black)](https://flask-sqlalchemy.readthedocs.io/en/stable/)
* [![Bootstrap][Bootstrap.com]][Bootstrap-url]
* [![JQuery][JQuery.com]][JQuery-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



# Flask Project

This is a Flask-based web application using MySQL, SQLAlchemy, Bootstrap, and Jinja2. It supports features like Google OAuth, file uploads, and email functionality. Follow the instructions below to set up the project locally.

## Getting Started

### Prerequisites

Make sure you have the following installed:
- Python 3.12 or higher
- MySQL Server
- pip (Python package manager)
- virtualenv (optional but recommended)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/aeydeee/Capstone_DoorLock.git
   cd your_repo_name
2. Set up a virtual environment (optional)
   ```sh
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate
   ```
3. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```
4. Set Up MySQL Database
   ```sh
   Create a MySQL database.
   Update .env with your database credentials:
   ```
   ```sh
   # .env file
   DB_USERNAME=your_username
   DB_PASSWORD=your_password
   DB_NAME=your_database_name
   DB_HOST=127.0.0.1
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://${DB_USERNAME}:${DB_PASSWORD}@localhost/${DB_NAME}
   ```
5. Set Up Other Environment Variables Update the .env file with the following:
   ```sh
   # .env file
   SECRET_KEY=your_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key
   UPLOAD_FOLDER=static/images/
   SESSION_TYPE=filesystem
   
   # Flask-Dance Google
   FLASK_APP=app.py
   GOOGLE_OAUTH_CLIENT_ID=your_client_id
   GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
   OAUTHLIB_RELAX_TOKEN_SCOPE=1
   OAUTHLIB_INSECURE_TRANSPORT=1

   # Google Drive
   DRIVE_FOLDER_ID=your_drive_folder_id

   FLASK_ENV=production

   # Mail
   MAIL_SERVER=smtp.your_email_provider.com
   MAIL_PORT=your_mail_port
   MAIL_USERNAME=your_email@example.com
   MAIL_PASSWORD=your_email_password
   MAIL_DEFAULT_SENDER=your_email@example.com
   MAIL_USE_TLS=True
   MAIL_USE_SSL=False
   ```
7. Run Database Migrations
   ```sh
   flask db upgrade
   ```
8. Run Database Migrations
   ```sh
   flask run
   ```


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Access the application in your browser at http://127.0.0.1:5000. Use the admin panel or routes to manage features.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Add more authentication options
- [ ] Enhance UI/UX with advanced Bootstrap components
- [ ] Add API support for external integrations
- [ ] Add a Frontend Framework like React

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are welcome! Follow these steps. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Adrian Samuel O. - [@aeydeee](https://m.me/aeydeee) - aeydeee@gmail.com

Project Link: [https://github.com/aeydeee/Capstone_DoorLock](https://github.com/aeydeee/Capstone_DoorLock)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
