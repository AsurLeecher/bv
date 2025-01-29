import base64
import json
import requests
import os
import re
from io import StringIO, BytesIO
from flask import Flask, render_template, request, send_file
from jinja2 import Template
from dotenv import load_dotenv
load_dotenv()

auth = os.environ['CHANDRA_API_AUTH']  # Will throw error if not set

app = Flask(__name__)

#auth = "7b81679d-a829-4476-8dcf-9c3bb4e0c80a"

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        return process_request(user, password)
    return render_template('index.html')

def process_request(user, password):
    try:
        # Login logic
        login_url = "http://api.chandrainstitute.com/api/v2/api.php/user/login"
        info = {"mobile": user, "password": password, "android_id": "asdasdasda"}
        res = requests.post(login_url, data=json.dumps(info), headers={"Auth": auth})
        
        if res.status_code != 200:
            return render_template('error.html', message="Login failed"), 401

        login_res = res.json()
        login_dict = login_res.get("response", {})
        u_id, token = login_dict.get("u_id"), login_dict.get("auth_token")

        # Get courses
        all_course_link = "http://api.chandrainstitute.com/api/v2/api.php/get/all/course"
        new_info = {"user_id": u_id, "course_type": "videos", "payment_type": "paid"}
        courses_res = requests.post(all_course_link, 
                                  data=json.dumps(new_info), 
                                  headers={"Auth": auth, "token": token})

        courses_dict = courses_res.json().get("response", [])
        
        # Create in-memory zip file
        zip_io = BytesIO()
        
        with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for course_dict in courses_dict:
                course_id = course_dict.get("cp_id")
                course_title = f"{course_id}. {course_dict.get('title', 'Untitled Course')}"
                safe_title = sanitize_filename(course_title)

                # Generate files in memory
                txt_content, html_content, json_content = process_course(
                    course_id, course_title, u_id, token
                )

                # Add files to zip
                zipf.writestr(f"{safe_title}/{safe_title}.txt", txt_content)
                zipf.writestr(f"{safe_title}/{safe_title}.html", html_content)
                zipf.writestr(f"{safe_title}/{safe_title}.json", json_content)

        zip_io.seek(0)
        return send_file(zip_io, 
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name='courses_data.zip')

    except Exception as e:
        return render_template('error.html', message=str(e)), 500

def process_course(course_id, course_title, u_id, token):
    # Your existing processing logic here
    # Return txt_content, html_content, json_content as strings
    # (Adapt your original file generation code to build strings instead of writing files)
    
    # Example structure:
    txt_content = StringIO()
    html_template = Template(open("templates/results.html").read())
    
    # Add your original processing logic here...
    
    return (
        txt_content.getvalue(),
        html_template.render(...),
        json.dumps(...)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
