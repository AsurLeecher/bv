import base64
import json
import requests
import re
from jinja2 import Template

# Function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

template = Template(open("template.html").read())
login_url = "http://api.chandrainstitute.com/api/v2/api.php/user/login"

user = input("Enter user_id/mobile: ")
password = input("Enter password: ")

info = {
    "mobile": user,
    "password": password,
    "android_id": "asdasdasda"
}

auth = "7b81679d-a829-4476-8dcf-9c3bb4e0c80a"
res = requests.post(login_url, data=json.dumps(info), headers={"Auth": auth})

# Check if login was successful
if res.status_code != 200:
    print("Login failed. Check your credentials.")
    exit()

login_res = res.json()
if "response" not in login_res:
    print("Invalid login response.")
    exit()

login_dict = login_res["response"]
u_id, token = login_dict["u_id"], login_dict["auth_token"]

all_course_link = "http://api.chandrainstitute.com/api/v2/api.php/get/all/course"
new_info = {
    "user_id": u_id,
    "course_type": "videos",
    "payment_type": "paid"
}

courses_res = requests.post(all_course_link, data=json.dumps(new_info), headers={"Auth": auth, "token": token})

courses_dict = courses_res.json().get("response", [])
for course_dict in courses_dict:
    course_id = course_dict.get("cp_id")
    course_title = course_dict.get("title", "Untitled Course")
    course_title = f"{course_id}. {course_title}"
    safe_course_title = sanitize_filename(course_title)
    
    # Create course-specific text file in write mode to avoid appending on multiple runs
    with open(f"{course_id}.txt", "w") as course_file:
        course_link = f"http://api.chandrainstitute.com/pdo/api/api.php/get/list/subjects/videos/all/{course_id}"
        course_res = requests.get(course_link, headers={"Auth": auth, "token": token})
        subjects = course_res.json().get("response", [])
        
        output_dict = {}
        for subject in subjects:
            subject_id = subject.get("subject_id")
            subject_name = subject.get("subject_name", "Untitled Subject")
            subject_title = f"{subject_id}. {subject_name}"
            
            subject_link = "http://api.chandrainstitute.com/api/v2/api.php/get/class/all/chapters/list"
            subject_info = {
                "course_id": course_id,
                "subject_id": subject_id,
                "u_id": u_id
            }
            subject_res = requests.post(subject_link, data=json.dumps(subject_info), headers={"Auth": auth, "token": token})
            chapters = subject_res.json().get("response", [])
            
            videos_dict = {}
            for chapter in chapters:
                chapter_name = chapter.get("chapter_name", "Untitled Chapter")
                youtube_id = chapter.get("youtubeId", "")
                video_id = base64.b64decode(youtube_id).decode("UTF-8") if youtube_id else ""
                video_link = f"https://youtu.be/{video_id}" if video_id else "#"
                videos_dict[chapter_name] = video_link
                course_file.write(f"{chapter_name}: {video_link}\n")
            
            output_dict[subject_title] = videos_dict
        
        # Write JSON file
        with open(f"{course_id}.json", "w") as json_file:
            json.dump(output_dict, json_file, indent=4)
        
        # Generate HTML file
        html_content = template.render(
            title=course_title,
            batch=course_title,
            topics=output_dict,
            type="videos"
        )
        with open(f"{safe_course_title}.html", "w") as html_file:
            html_file.write(html_content)
        
        print(f"Processed: {course_title}")

print("\n" + " Finished ".center(60, "-"))
