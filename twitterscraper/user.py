from bs4 import BeautifulSoup
import requests
from query import HEADERS_LIST
from query import HEADER

from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options

class User:
    def __init__(self, user=None, full_name="", location="", blog="", date_joined=None, id=None, tweets=0, 
        following=0, followers=0, likes=0, lists=0, bio="", follower_list = [], following_list = []):
        self.user = user
        self.full_name = full_name
        self.location = location
        self.blog = blog
        self.date_joined = date_joined
        self.id = id
        self.tweets = tweets
        self.following = following
        self.followers = followers
        self.likes = likes
        self.lists = lists
        self.bio = bio
        self.follower_list = follower_list
        self.following_list = following_list
        

    def from_soup(self, tag_prof_header, tag_prof_nav):
        """
        Returns the scraped user data from a twitter user page.

        :param tag_prof_header: captures the left hand part of user info
        :param tag_prof_nav: captures the upper part of user info
        :return: Returns a User object with captured data via beautifulsoup
        """

        self.user= tag_prof_header.find('a', {'class':'ProfileHeaderCard-nameLink u-textInheritColor js-nav'})['href'].strip("/") 
        
        self.follower_list, self.following_list = self.fetch_followers_and_following()
        
        
        self.full_name = tag_prof_header.find('a', {'class':'ProfileHeaderCard-nameLink u-textInheritColor js-nav'}).text
        
        location = tag_prof_header.find('span', {'class':'ProfileHeaderCard-locationText u-dir'}) 
        if location is None:
            self.location = "None"
        else: 
            self.location = location.text.strip()

        blog = tag_prof_header.find('span', {'class':"ProfileHeaderCard-urlText u-dir"})
        if blog is None:
            blog = "None"
        else:
            self.blog = blog.text.strip() 

        date_joined = tag_prof_header.find('div', {'class':"ProfileHeaderCard-joinDate"}).find('span', {'class':'ProfileHeaderCard-joinDateText js-tooltip u-dir'})['title']
        if date_joined is None:
            self.data_joined = "Unknown"
        else:    
            self.date_joined = date_joined.strip()

        self.id = tag_prof_nav.find('div',{'class':'ProfileNav'})['data-user-id']
        tweets = tag_prof_nav.find('span', {'class':"ProfileNav-value"})['data-count']
        if tweets is None:
            self.tweets = 0
        else:
            self.tweets = int(tweets)

        following = tag_prof_nav.find('li', {'class':"ProfileNav-item ProfileNav-item--following"}).\
        find('span', {'class':"ProfileNav-value"})['data-count']
        if following is None:
            following = 0
        else:
            self.following = int(following)

        followers = tag_prof_nav.find('li', {'class':"ProfileNav-item ProfileNav-item--followers"}).\
        find('span', {'class':"ProfileNav-value"})['data-count']
        if followers is None:
            self.followers = 0
        else:
            self.followers = int(followers)    
        
        likes = tag_prof_nav.find('li', {'class':"ProfileNav-item ProfileNav-item--favorites"}).\
        find('span', {'class':"ProfileNav-value"})['data-count']
        if likes is None:
            self.likes = 0
        else:
            self.likes = int(likes)    
        
        lists = tag_prof_nav.find('li', {'class':"ProfileNav-item ProfileNav-item--lists"})
        if lists is None:
            self.lists = 0
        elif lists.find('span', {'class':"ProfileNav-value"}) is None:    
            self.lists = 0
        else:    
            lists = lists.find('span', {'class':"ProfileNav-value"}).text    
            self.lists = int(lists)
        
        # Fetch user bio
        bio = tag_prof_header.find('p', {'class':'ProfileHeaderCard-bio u-dir'})
        if bio:
            self.bio = bio.text
                
        return(self)
    
    # intialize driver and log in to Twitter
    def initialize_driver(self, disable_gpu=True):
        options = Options()
        if disable_gpu:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
        
        # create new Chrome session
        driver = webdriver.Chrome(chrome_options=options)
        
        # navigate to the application home page
        driver.get("https://twitter.com/login")


        # get the username textbox
        login_field = driver.find_element_by_class_name("js-username-field")
        login_field.clear()

        # enter username
        login_field.send_keys("Michael90482875")
        #time.sleep(1)

        #get the password textbox
        password_field = driver.find_element_by_class_name("js-password-field")
        password_field.clear()

        #enter password
        password_field.send_keys("Iam4IRISH11")
        #time.sleep(1)
        password_field.submit()
        return driver

    # helper to scroll to the bottom of an infinite scroll
    def scroll_to_end(self, driver):
        SCROLL_PAUSE_TIME = 0.5
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height, compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        return

    # Assumes user param of self has already been set.
    # returns: followers_list (list of user names, strings)
    #          following_list (list of user names, strings)
    def fetch_followers_and_following(self):
        if self.user == None:
            return [], []
        driver = self.initialize_driver()

        # generate followers
        url = "https://twitter.com/{}/followers".format(self.user)
        followers = self.list_from_url(driver, url)
        url = "https://twitter.com/{}/following".format(self.user)
        following = self.list_from_url(driver, url)

        return followers, following

    def list_from_url(self, driver, url):
        res = []
        driver.get(url)
        
        # make sure all elements are revealed by scrolling to end
        self.scroll_to_end(driver)

        soup = BeautifulSoup(driver.page_source, 'lxml')
        user_tag_list = soup.find_all("b", {"class", "u-linkComplete-target"})

        # turn HTML into username
        for user_tag in user_tag_list:
            if user_tag == self.user:
                continue
            res.append(user_tag.contents)
        return res

    def from_html(self, html):
        soup = BeautifulSoup(html, "lxml")
        user_profile_header = soup.find("div", {"class":'ProfileHeaderCard'})
        user_profile_canopy = soup.find("div", {"class":'ProfileCanopy-nav'})
        if user_profile_header and user_profile_canopy:
            try:
                return self.from_soup(user_profile_header, user_profile_canopy)
            except AttributeError:
                pass  # Incomplete info? Discard!
            except TypeError:
                pass  # Incomplete info? Discard!
