# Blog Project

## Description
Welcome to the **Blog Project**, a fully functional and dynamic blog website built using Flask, Python, Bootstrap, 
HTML, CSS, JavaScript, and SQLite (for development) / PostgreSQL (for production). This project is designed to provide
a seamless blogging experience with user authentication, commenting functionality, contact form for communication,
search functionality, and relational database management.
The site is hosted on **Render**, making it accessible to users worldwide. It's designed to provide a platform for 
sharing articles, engaging with readers through comments, and facilitating communication via a contact form.


## Table of Contents
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Credits](#credits)
- [License](#license)

## Features
**User Authentication**:
- Signing Up: users can swiftly register and log in. Authenticated users can leave comments on articles, fostering 
        engagement and discussion. Comments are stored in the database and displayed in real-time. 
- Secure Authentication: passwords are securely hashed and salted with werkzeug security, using industry-standard 
        practices to ensure user data safety.

**Dynamic Sections**:
- Several dynamic forms are being used: register, login, create/edit post, delete post. Only admin has create / edit /delete
post rights. Safety measure for deleting posts - a deletion code must be input.

**Search Functionality**:
- Any visitor can search articles and comments to articles by keywords.

**Flask WTForms (forms.py)**:
- Post Form - uses CKEditor 4.14.0 free version (disregard the update warning) for text formatting control. 
  Provides the UI for creating new posts and editing already published ones.
- Registration Form - for users registration in the database (users.tbl - see class User). Password encrypted and salted with `werkzeug.security`, `salt length=10`
- Login Form - for users authentication
- Comment Form - logged-in user can submit comments to each post.
- Contact Form using SMTP integration allows visitors to send emails directly to the site administrator (see below about `ADMIN_EMAIL` env var).


**Responsive Design**:
- Implemented with Bootstrap, it ensures a consistent UX/UI across various devices (mobile, tablet, laptop, desktop).
    Custom CSS and JavaScript enhance the user experience and add interactivity.

**Database Management**:
- Development: SQLite is used for local development, providing a lightweight and easy-to-use database solution.
- Production: PostgreSQL is used in production for scalability, reliability, and performance.
    
**Deployment Ready**:
- It is hosted on Render, a modern cloud platform that ensures high availability and fast load times. 
- The deployment process is streamlined, with automatic updates from the linked repository.

## Technologies
- Backend: Flask Python
- Frontend: HTML5, CSS3, Bootstrap5, JavaScript
- Databases: SQLAlchemy (ORM), SQLite (development), PostgreSQL (production)
- Hosting: Render
- Email Service: SMTP
- Version Control: GitHub


## Installation
### Prerequisites
- Python 3.13
- Pip (Python package manager)
- Virtual environment (recommended)
- DB Browser for SQLite (recommended) - for interacting with the local database https://sqlitebrowser.org/dl/
- PostgreSQL (for production)
- pgAdmin4 - recommended for direct interaction with PostgreSQL database https://www.pgadmin.org/download/

### Steps to Run Locally
1. Clone the Repository:
    ```bash
    git clone https://github.com/Nina-C4/Blog_Project.git
    cd blog-project
    ```
   
2. Create a Virtual Environment in your favourite IDE (e.g. PyCharm, VS Code):
    ```bash
    python -m venv venv
    ```
 
3. Activate the Virtual Environment:
    * Windows: `venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`

4. Install Dependencies:
    ```bash
    pip install -r requirements.txt
    ```

5. Set Up Environment Variables:  
   Create a `.env` file in the root directory. You will need to set the following variables:  
   *Flask framework and databases:*  
   - `SECRET_KEY`: set a Flask app key used for CSRF (a long alphanumeric password) 
   - `DB_URI`: sqlite:///your_path_to_project/instance/blog_posts.db (for development)
   - `DATABASE_URL`: Render Dashboard > Your PostgreSQL DB > scroll down to Connections > Copy `Internal Database URL`

   *Database choice:*  
   - `LOCAL`: `True` to run the app in your browser, using SQLite database  
   ! Note: when configuring PostgreSQL on Render, this env var must be set to `False`

   *Email functionality to send notifications (e.g. new subscriber alerts):* 
   - `APP_EMAIL`: The email address that the application will use to send emails. This is typically your application's "from" address.
   - `PASS`: The password for the email address specified in `APP_EMAIL`. 
   - `ADMIN_EMAIL`: The email address that will receive notifications from the blog. This is typically your admin/personal email address.

   *Delete records in databases* - admin privilege
   - `DELETION_CODE`: blog posts can be deleted only by the admin; as an error-proof and security measure, after pressing the `✘` sign, they will be required to enter this code before confirming post deletion.  
   
   Example code for `.env`:
   ```plaintext
    SECRET_KEY=Fj8Rbyl1knfzWl3SihBof9Cgq
    DB_URI=sqlite:///C:/Users/username/PycharmProjects/Blog_Project/instance/blog_posts.db
    DATABASE_URL=postgresql://username:password@hostname:5432/dbname
    APP_EMAIL=your_coding_email@gmail.com
    PASS=mtdfgvtnjrvjp    # generated in the G_account of APP_EMAIL
    ADMIN_EMAIL=your_personal_email@gmail.com
    DELETION_CODE=a1D6m1i8N0
    LOCAL=True
   ```

6. Initialize the Database:  
   The SQLite local database and tables will be created at the first application run of `main.py`

7. Run the Application in browser:
   ```bash
   flask run
   ```
   Go to `http://localhost:5000/` in your preferred browser to view the blog.

8. Create the first `User`
   Go to `http://localhost:5000/register` and fill in the *RegistrationForm* to create the first user.
   User with id=1 is set as site admin, with full rights to create/edit/delete posts from database.
   
9. Create your first `BlogPost`
   Logged in as admin, after registration, go to http://localhost:5000/ and `Create New Post`.

### Deployment to Render

1. **Create Procfile**:
   Create new file in project root directory named Procfile and add reference to gunicorn.
   ```plaintext
     web: gunicorn main:app
     ```

2. **Push to GitHub**:
   Ensure your project is pushed to a GitHub repository.

3. **Create a Render Postgre Database and Web Service**:
   - Log in to Render and create a new **Web Service**.
   - Connect your GitHub repository.
   - Set the following environment variables in the Render dashboard:
     ```plaintext
     SECRET_KEY=your_secret_key
     DATABASE_URL=your_postgresql_internal_url
     APP_EMAIL=your_coding_email@gmail.com
     PASS=your_APP_EMAIL_password
     ADMIN_EMAIL=your_personal_email@gmail.com
     DELETION_CODE=your_deletion_code
     LOCAL=False
     ```

4. **Render Deployment (Production)**:
   Render will automatically install dependencies and run migrations based on the `requirements.txt` and specified commands. 
   Once deployed, your blog will be live at the provided Render URL.


## Usage

Provide instructions and examples for use. Include screenshots as needed.

To add a screenshot, create an `assets/images` folder in your repository and upload your screenshot to it. Then, using the relative filepath, add it to your README using the following syntax:

    ```md
    ![alt text](assets/images/screenshot.png)
    ```

## Credits
[Angela Yu](https://www.udemy.com/course/100-days-of-code/)

---

## License
MIT License

Copyright (c) 2025 | Nina Patru

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
---



