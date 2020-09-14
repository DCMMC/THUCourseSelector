import json
import random
import datetime
import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# https://market.aliyun.com/products/57124001/cmapi00035185.html
captcha_appcode = open('captcha_appcode.txt').read().strip()
u, p = input('User: '), input('Password: ')
# driver = webdriver.Chrome()
driver = webdriver.Firefox()
# driver.implicitly_wait(60 * 5)
wait = WebDriverWait(driver, 100)
# 两次操作的间隔不能小于 3s
delay = [3, 5]
max_tries = 199
max_loop = 500
obj_courses = {}
for line in open('objects.txt').readlines():
    if not line[0] == '#':
        course_id, class_id = map(lambda s: int(s) if s.isdigit() else s,
                                  line.strip().split()[:2])
        if course_id in obj_courses:
            obj_courses[course_id].append(class_id)
        else:
            obj_courses[course_id] = [class_id]


def get_captcha(captcha_base64):
    test_url = 'http://codevirify.market.alicloudapi.com/icredit_ai_image/verify_code/v1'
    headers = {
        'Authorization': 'APPCODE %s' % captcha_appcode,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    data = {'IMAGE': captcha_base64, 'IMAGE_TYPE': '0'}
    resp = requests.post(test_url, headers=headers, data=data)
    captchacode = json.loads(resp.text)['VERIFY_CODE_ENTITY']['VERIFY_CODE']
    return captchacode.upper()


for loop in range(max_loop):
    while 'xkYjs.vxkYjsXkbBs.do' not in driver.current_url:
        driver.get('http://zhjwxk.cic.tsinghua.edu.cn/xklogin.do')
        wait.until(EC.presence_of_element_located(
            (By.ID, '_login_image_')))
        user = driver.find_element_by_name('j_username')
        passwd = driver.find_element_by_name('j_password')
        capt = driver.find_element_by_name('_login_image_')
        captcha_base64 = driver.find_element_by_id(
            'captcha').screenshot_as_base64
        captcha = get_captcha(captcha_base64)

        btn_login = driver.find_element_by_css_selector(
            'a[onclick^="doLogin();"]').find_element_by_tag_name('img')
        coordinates = btn_login.location_once_scrolled_into_view
        driver.execute_script('window.scrollTo({}, {});'.format(
            coordinates['x'], coordinates['y']))
        user.send_keys(u)
        passwd.send_keys(p)
        capt.send_keys(captcha)
        btn_login.click()
        sleep(2)
    driver.switch_to.default_content()
    try:
        wait.until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, 'frame[name^="tree"]')))
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[onclick^="showhidediv()"]')))
        driver.find_element_by_css_selector('a[onclick^="showhidediv()"]').click()
        wait.until(
            EC.presence_of_element_located(
                (By.LINK_TEXT, '选课')))
        driver.find_element_by_link_text('选课').click()
    except TimeoutException:
        print('timeout, continue')
        continue
    for cnt in range(1, random.randint(max_tries - 5, max_tries)):
        driver.switch_to.default_content()
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, 'frame[name^="right"]')))
        except TimeoutException:
            print('timeout, continue')
            continue
        if len(driver.find_elements_by_css_selector(
                'font[size="5px"][color="#595959"]')):
            print('选课尚未开始, 10s 后重试')
            sleep(10)
            driver.switch_to.default_content()
            try:
                wait.until(EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, 'frame[name^="tree"]')))
                driver.find_element_by_link_text('选课').click()
            except TimeoutException:
                pass
            sleep(1)
            continue
            # sys.exit(-1)
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, 'iframe[name^="fcxkFrm"]')))
            wait.until(EC.presence_of_element_located(
                (By.TAG_NAME, 'body')))
            wait.until(EC.presence_of_element_located(
                (By.ID, 'table_t')))
        except TimeoutException:
            print('timeout, continue')
            continue
        # 每次登陆后最多 200 次操作
        if '您本次登录后操作过于频繁' in driver.find_element_by_tag_name(
                'body').get_attribute('innerHTML'):
            break
        for clazz in driver.find_element_by_id(
                'table_t').find_elements_by_css_selector(
                    'input[type^="checkbox"]'):
            course_id, class_id = map(
                int,
                clazz.get_attribute('value').split(';')[1:3])
            if class_id >= 200 and course_id in obj_courses and \
                    (class_id in obj_courses[course_id] or '*' in obj_courses[course_id]):
                coordinates = clazz.location_once_scrolled_into_view
                driver.execute_script('window.scrollTo({}, {});'.format(
                    coordinates['x'], coordinates['y']))
                clazz.click()
        driver.switch_to.default_content()
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, 'frame[name^="right"]')))
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, 'iframe[name^="fcxkFrm"]')))
        except TimeoutException:
            print('timeout, continue')
            continue
        btn_commit = driver.find_element_by_css_selector(
            'input[onclick^="commitFcxAdd()"]')
        coordinates = btn_commit.location_once_scrolled_into_view
        driver.execute_script('window.scrollTo({}, {});'.format(
            coordinates['x'], coordinates['y']))
        btn_commit.click()

        try:
            wait.until(
                EC.alert_is_present(),
                'Timeout waiting for commiting respond.')
            alert = driver.switch_to.alert
            print('Commiting respond:', '\n'.join(alert.text.split('!')))
            alert.accept()
        except TimeoutException:
            print('Timeout waiting for commiting respond.')
            continue
        except Exception as e:
            print('Exception:', e)

        now = datetime.datetime.now()
        today7am = now.replace(hour=7, minute=0, second=0)
        today2am = now.replace(hour=2, minute=0, second=0)
        if today2am <= now < today7am:
            # delay for 4.5hrs
            delay[0] += 60 * 60 * 4.5
            delay[1] += 60 * 60 * 4.5
        curr_delay = random.randint(*delay)
        print('Waiting for {}s.'.format(curr_delay))
        sleep(curr_delay)
    print(f'End of Loop {loop}')
