importimport time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

DOCKER_IMAGE = "docker.io/seifszx/seifszx"

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--remote-debugging-port=9222")
    options.binary_location = "/usr/bin/google-chrome"
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver

def wait_and_click(driver, by, selector, timeout=30):
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, selector))
    )
    element.click()
    return element

def wait_for_element(driver, by, selector, timeout=30):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )

def process_link(url: str) -> dict:
    driver = None
    try:
        driver = get_driver()
        logger.info(f"فتح الرابط: {url}")
        driver.get(url)
        time.sleep(3)

        # ===== المرحلة 1: قبول "أفهم ذلك" من Google =====
        try:
            logger.info("انتظار صفحة الترحيب من Google...")
            # زر "أفهم ذلك" - يظهر باللغة العربية أو الإنجليزية
            accept_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(., 'أفهم ذلك') or contains(., 'I understand') or contains(., 'Got it')]"
                ))
            )
            accept_btn.click()
            logger.info("✅ تم الضغط على 'أفهم ذلك'")
            time.sleep(3)
        except TimeoutException:
            logger.info("صفحة الترحيب لم تظهر، المتابعة...")

        # ===== المرحلة 2: قبول شروط Google Cloud =====
        try:
            logger.info("انتظار شروط Google Cloud...")
            
            # الضغط على Checkbox الأول "I agree to the Google Cloud Platform Terms"
            checkbox = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH,
                    "//input[@type='checkbox'][1] | //mat-checkbox[1]"
                ))
            )
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
            logger.info("✅ تم تحديد checkbox الشروط")
            time.sleep(1)

            # الضغط على "Agree and continue"
            agree_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(., 'Agree and continue')]"
                ))
            )
            agree_btn.click()
            logger.info("✅ تم الضغط على 'Agree and continue'")
            time.sleep(4)

        except TimeoutException:
            logger.info("شروط Google Cloud لم تظهر، المتابعة...")

        # ===== المرحلة 3: الذهاب إلى Cloud Run > Services =====
        logger.info("الذهاب إلى Cloud Run Services...")
        
        # فتح القائمة الجانبية
        try:
            menu_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Main menu']"))
            )
            menu_btn.click()
            time.sleep(2)
        except:
            # محاولة بطريقة أخرى
            driver.get(driver.current_url.split('/home')[0] + '/run/services')
            time.sleep(3)

        # البحث عن Cloud Run في القائمة
        try:
            cloud_run = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Cloud Run')]"))
            )
            cloud_run.click()
            time.sleep(1)
            
            # اختيار Services
            services = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Services')]"))
            )
            services.click()
            time.sleep(3)
        except:
            # الذهاب مباشرة عبر URL
            current_url = driver.current_url
            project_id = extract_project_id(current_url)
            driver.get(f"https://console.cloud.google.com/run?project={project_id}")
            time.sleep(3)

        # ===== المرحلة 4: إنشاء Service =====
        logger.info("الضغط على Create Service...")
        
        create_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[contains(., 'Create service') or contains(., 'Create Service')]"
            ))
        )
        create_btn.click()
        time.sleep(4)

        # ===== المرحلة 5: ملء نموذج Create Service =====
        logger.info("ملء نموذج الخدمة...")

        # إدخال Container Image URL
        image_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH,
                "//input[@placeholder='Container image URL' or @aria-label='Container image URL']"
            ))
        )
        image_input.clear()
        image_input.send_keys(DOCKER_IMAGE)
        logger.info(f"✅ تم إدخال الصورة: {DOCKER_IMAGE}")
        time.sleep(1)

        # Billing: Instance-based
        try:
            instance_based = driver.find_element(By.XPATH,
                "//input[@type='radio'][following-sibling::*[contains(., 'Instance-based')] or @value='instance']"
            )
            driver.execute_script("arguments[0].click();", instance_based)
            logger.info("✅ تم اختيار Instance-based")
            time.sleep(1)
        except:
            logger.warning("لم يتم العثور على Instance-based radio")

        # Authentication: Allow public access
        try:
            public_access = driver.find_element(By.XPATH,
                "//input[@type='radio'][following-sibling::*[contains(., 'Allow unauthenticated')] or contains(@value, 'public')]"
            )
            driver.execute_script("arguments[0].click();", public_access)
            logger.info("✅ تم اختيار Allow public access")
            time.sleep(1)
        except:
            logger.warning("لم يتم العثور على public access radio")

        # Minimum instances: 1
        try:
            min_input = driver.find_element(By.XPATH,
                "//input[@aria-label='Minimum number of instances' or @placeholder='0']"
            )
            min_input.clear()
            min_input.send_keys("1")
            logger.info("✅ تم إدخال Minimum: 1")
            time.sleep(0.5)
        except:
            logger.warning("لم يتم العثور على minimum instances input")

        # Maximum instances: 16
        try:
            max_input = driver.find_element(By.XPATH,
                "//input[@aria-label='Maximum number of instances']"
            )
            max_input.clear()
            max_input.send_keys("16")
            logger.info("✅ تم إدخال Maximum: 16")
            time.sleep(0.5)
        except:
            logger.warning("لم يتم العثور على maximum instances input")

        # الضغط على Create
        logger.info("الضغط على Create...")
        create_final = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[text()='Create' or normalize-space(text())='Create']"
            ))
        )
        create_final.click()
        logger.info("✅ تم الضغط على Create")
        time.sleep(5)

        # ===== المرحلة 6: انتظار الـ Endpoint URL =====
        logger.info("انتظار Endpoint URL...")
        endpoint_url = None
        
        for _ in range(30):  # انتظر حتى 5 دقائق
            try:
                url_element = driver.find_element(By.XPATH,
                    "//a[contains(@href, '.run.app')] | //span[contains(text(), '.run.app')]"
                )
                endpoint_url = url_element.text or url_element.get_attribute("href")
                if endpoint_url:
                    logger.info(f"✅ تم الحصول على Endpoint URL: {endpoint_url}")
                    break
            except NoSuchElementException:
                pass
            time.sleep(10)

        if not endpoint_url:
            # محاولة أخيرة من الـ URL الحالي
            current = driver.current_url
            if "run.app" in current:
                endpoint_url = current

        if endpoint_url:
            return {"success": True, "endpoint_url": endpoint_url}
        else:
            return {"success": False, "error": "لم يتم العثور على Endpoint URL"}

    except Exception as e:
        logger.error(f"خطأ في process_link: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_project_id(url: str) -> str:
    """استخراج project ID من الـ URL"""
    import re
    match = re.search(r'project=([^&]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'qwiklabs-gcp-[a-z0-9-]+', url)
    if match:
        return match.group(0)
    return ""
