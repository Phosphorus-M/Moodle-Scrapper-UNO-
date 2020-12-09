import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import lxml
from lxml import html
import random
from urllib.request import urlretrieve
import time
import os
from clint.textui import progress

#import necessary packages


#User data. Noob level. Make this more secure later
#username = input("Enter Moodle Username")
#password = input("Enter Password")

cred = open("pass.txt", "r")
user = str(cred.readline().rstrip("\n"))
pas = str(cred.readline().rstrip("\n"))
print(user)
print(pas)
payload = {'username':user, 'password':pas}


#2 sites needed. One is the login page and the other is the page from where to start data collection
login_site = (r"http://campusvirtual.uno.edu.ar/moodle/login/index.php")
data_site = (r"http://campusvirtual.uno.edu.ar/moodle/my/")

#Make a requests Session and input the login data and get the text on the page

with requests.Session() as session:
    post = session.post(login_site, data=payload)
    r = session.get(data_site)
    content = r.text
    # print(content)

#Make a Beasutiful Soup object and write contents to a file

soup = BeautifulSoup(content, 'lxml')

moo = open("Moodle.txt", 'w')
#moo.write(soup.prettify())

#Inspect element from website to find out what type of tag our data is in and use find that tag
#Below code finds 8 tags for 8 courses
#course_tags is a bs4 Result set

course_tags = soup.find_all('h2', 'title')
print("Courses: " + str(len(course_tags)))

#Make a dictionary to update all the individual links of the subjects
link_dict = {}
course_links = []

for c in course_tags:
    for i in c.children:
        #print("Madre mia chaval" + str(i) if i!='\n' else '')
        href = i['href']
        c_name  = i.text
        #print(i.text)
        # print("we " + href)
        course_links.append(href)
        link_dict[href] = c_name

# print(link_dict)

#link_dict now contains all the links to the registered courses for a person for  this semester

#print(evs)

#This function is to get all the resource links in a particular course
def links_in_course(course_link):

    course_page = session.get(course_link)
    course_page_content_soup = BeautifulSoup(course_page.text,'lxml')

    resource_links = course_page_content_soup.find_all('li', class_ ='activity resource modtype_resource')
    resource_links_2 = []
    file_types = []

    print(resource_links[0])
    for li in resource_links:
        r_tags = li.find_all('a')
        if(len(r_tags) == 0):   
            continue

        r_link = r_tags[0]['href']

        img_tags = li.find_all('img')
        img_link = img_tags[0]['src']

        if 'folder' in img_link:
            f_type = 'folder'
        else:
            f_type = 'archive'

        #file_name_tags =  []
        for a_tag in r_tags:
            file_name_tags = a_tag.find('span', class_ = 'instancename')
            if file_name_tags is not None:
                file_name = file_name_tags.contents[0]


        resource_links_2.append([r_link,f_type,file_name])



    moo.write(str(resource_links_2))

    return resource_links_2

def download_archive(pg_link, file_name,subj_path):
    #Getting the name of file
    archive_page = session.get(pg_link, stream=True)
    file_extension = archive_page.url.split('.')[-1]
    f_path = file_name+ "." +file_extension
    f_path = f_path.replace('/', '-')

    full_path = os.path.join(subj_path,f_path)
	
    # Printing something lpm
    print(pg_link+'  -----  '+f_path+' 📩')
    if os.path.exists(full_path):
        print('~~~~~~~~  already exists, skiping  ~~~~~~~~')
        return

    with open(full_path, 'wb') as f:
        total_length = int(archive_page.headers.get('content-length'))
        for chunk in progress.bar(archive_page.iter_content(chunk_size=1024), expected_size=(total_length/1024)+1):
            if chunk:
                f.write(chunk)
                f.flush()
        print('Downloaded                                                   ✅')

#This function downloads all the resources(word,pdf,ppt)
def download_resources(links,subj_path):

    time.sleep(1)

    for resource in links:

        if(resource[1] is not None):
            download_archive(resource[0],resource[2],subj_path)
            time.sleep(5) # prevent rate-limiting
        else:
            print("No resource to download")


    print("All downloads Completed")


def download_from_folder(course_link, subj_path):
    course_page = session.get(course_link)
    course_page_content_soup = BeautifulSoup(course_page.text,'lxml')

    resource_links = course_page_content_soup.find_all('li', class_ ='activity folder modtype_folder')
    file_names = []
    r_links = []
    for li in resource_links:

        folder_tags = li.find_all('a')
        folder_link = folder_tags[0]['href']

        folder_page = session.get(folder_link)
        folder_page_soup = BeautifulSoup(folder_page.text, 'lxml')

        inside_link = folder_page_soup.find_all('span', class_ = 'fp-filename-icon')

        for span in inside_link:
            a_link = span.find('a')
            r_link = a_link['href']

            r_links.append(r_link)

        name_link = folder_page_soup.find_all('span', class_ = "fp-filename")

        for files in name_link[1:]:
            file_names.append(files.string)



    new_dict = dict(zip(r_links, file_names))

    for item in new_dict:

        time.sleep(1)

        f_path = new_dict[item]
        full_path = os.path.join(subj_path,f_path)

        down_page = session.get(item)
        if not os.path.exists(full_path):
            open(full_path, 'wb').write(down_page.content)

        #open(file_name+'.ppt','wb').write(down_page.content)

            print("Downloaded " + new_dict[item])


def make_folders(link_dict):
    print(link_dict)
    subject_paths = {}
    for item in link_dict:

        course_name = link_dict[item]
        print(course_name)

        path = os.getcwd()
        subject_path = os.path.join(path,"Moodle Materials", course_name)
        subject_paths[course_name] = subject_path

        if not os.path.exists(subject_path):
            os.makedirs(subject_path)

    return subject_paths

#print((sub_paths))

def main_function(link_dict,sub_paths):

    for item in link_dict:
        time.sleep(10) # prevent rate-limiting
        each_subject_folder_path = sub_paths[link_dict[item]]

        links_in_each_course = links_in_course(item)
        time.sleep(random.randint(500, 2000) / 1000) # prevent rate-limiting
        download_resources(links_in_each_course,each_subject_folder_path)
        time.sleep(5) # prevent rate-limiting
        download_from_folder(item,each_subject_folder_path)

        print("Downloads completed for ",link_dict[item])

    print("All Downloads Completed for All Subjects!")


sub_paths = make_folders(link_dict)
main_function(link_dict, sub_paths)
