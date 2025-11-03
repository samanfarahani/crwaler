import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import logging
import json
import os
from uuid import uuid4
import re
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter


class AdvancedVapeScraper:
    def __init__(self, job_id=None):
        self.job_id = job_id or str(uuid4())
        self.driver = None
        self.products_data = []
        self.is_running = False
        self.current_site = ""
        self.site_configs = {}
        self.setup_logging()
        self.setup_driver()
        self.setup_site_configs()
        
        os.makedirs('tmp_jobs', exist_ok=True)
    
    def setup_driver(self):
        """تنظیمات WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            # options.add_argument('--headless')  # در صورت نیاز فعال کنید
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(5)
            
            logging.info("✅ درایور راه‌اندازی شد")
            
        except Exception as e:
            logging.error(f"❌ خطا در راه‌اندازی درایور: {e}")
            raise
    
    def setup_site_configs(self):
        """پیکربندی دقیق برای 7 سایت هدف"""
        self.site_configs = {
            'dokhanmarket': {
                #دخان مارکت
                'name': 'Dokhan Market',
                'base_urls': ['https://dokhanmarket3.com', 'http://dokhanmarket3.com'],
                'category_selectors': [
                    'a[href*="category"]',
                    '.menu-link',
                    'nav a',
                    '.product-category a'
                ],
                'product_selectors': [
                    '.product-card',
                    '.product',
                    '.product-item',
                    '.goods-item'
                ],
                'name_selectors': [
                    '.product-card_link',
                    '.product-title',
                    'h3',
                    'h2',
                    '.product-name'
                ],
                'price_selectors': [
                    '.product-card_price',
                    '.price',
                    '.woocommerce-Price-amount',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    'a[href*="page="]',
                    '.next',
                    '.pagination-next',
                    'a.next'
                ],
                'next_text': ['بعدی', 'next', '→'],
                'category_keywords': ['category', 'cat', 'product-category', 'shop']
            },
            'tajvape': {
                #تاج ویپ
                'name': 'Tajvape',
                'base_urls': ['https://tajvape12.com', 'http://tajvape12.com'],
                'category_selectors': [
                    '.dropdown-toggle.menu-link',
                    '.menu-link',
                    'nav a',
                    '.product-category a',
                    'a[href*="product-category"]'
                ],
                'product_selectors': [
                    'ul.products columns-4',
                    'li.col-md-3 col-6 mini-product-con type-product',
                    '.product-link',
                    '.col-md-3 col-6 mini-product-con type-product',
                    
                    'div.woocommerce shadow-box prblur mini-product product-112542 prod-variable',
                    '.product',
                    '.product-item',
                    '.woocommerce-product',
                    'li.product'
                ],
                'name_selectors': [
                    '.product-title',
                    'h2',
                    'h3',
                    '.woocommerce-loop-product__title'
                ],
                'price_selectors': [
                    '.woocommerce-Price-amount',
                    '.price',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    '.next.page-numbers',
                    '.pagination a',
                    'a.next',
                    'a[href*="page/"]'
                ],
                'next_text': ['→', 'next', 'بعدی'],
                'category_keywords': ['product-category', 'category', 'e-juice', 'vape']
            },
            'vapoursdaily': {
                #ویپرز دیلی
                'name': 'Vapours Daily',
                'base_urls': ['https://vapoursdaily14.com', 'http://vapoursdaily14.com'],
                'category_selectors': [
                    '.menu-item a',
                    'nav a',
                    '.product-category a',
                    'a[href*="category"]'
                ],
                'product_selectors': [
                    '.product',
                    '.product-item',
                    '.woocommerce-product',
                    '.goods-item'
                ],
                'name_selectors': [
                    '.product-tittle',
                    'h3',
                    'h2',
                    '.product-name'
                ],
                'price_selectors': [
                    '.woocommerce-Price-amount',
                    '.price',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    '.next.page-numbers',
                    '.pagination a',
                    'a.next'
                ],
                'next_text': ['←', 'next', 'بعدی'],
                'category_keywords': ['product-category', 'category', 'vape']
            },
            'smokcenter': {
                #اسموک سنتر
                'name': 'Smok Center',
                'base_urls': ['https://smokcenter16.com', 'http://smokcenter16.com'],
                'category_selectors': [
                    'spen.elementor-icon-list-icon',
                    'spen.elementor-icon-list-text',
                    'li.elementor-icon-list-item',
                    'div.elementor-icon-wrapper',
                    '.elementor-icon',
                    '.e-n-tab-title-text',
                    'e-n-tab-title-3544064532.',
                    '.e-n-tab-title',
                    
                    '.wd-nav-products-cats a',
                    'nav a',
                    '.category-item a',
                    'a[href*="category"]'
                ],
                'product_selectors': [
                    '.product',
                    '.product-item',
                    '.wd-entities-title',
                    '.goods-item'
                ],
                'name_selectors': [
                    '.wd-entities-title',
                    'h3',
                    'h2',
                    '.product-title'
                ],
                'price_selectors': [
                    '.woocommerce-Price-amount',
                    '.price',
                    'ins .amount',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    '.load-more-label',
                    '.next',
                    '.pagination a',
                    'a[href*="page"]'
                ],
                'next_text': ['بارگیری بیشتر محصولات', 'next', 'بعدی'],
                'category_keywords': ['shop', 'category', 'ejuice']
            },
            'digizima': {
                #دیجی زیما
                'name': 'Digi Zima',
                'base_urls': ['https://digizima19.com', 'http://digizima19.com'],
                'category_selectors': [
                    '.menu-item a',
                    'nav a',
                    '.product-category a',
                    'a[href*="category"]'
                ],
                'product_selectors': [
                    '.product',
                    '.product-item',
                    '.wd-entities-title',
                    '.goods-item'
                ],
                'name_selectors': [
                    '.wd-entities-title',
                    'h3',
                    'h2',
                    '.product-name'
                ],
                'price_selectors': [
                    '.woocommerce-Price-amount',
                    '.price',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    '.next.page-numbers',
                    '.pagination a',
                    'a.next'
                ],
                'next_text': ['→', 'next', 'بعدی'],
                'category_keywords': ['product-category', 'category', 'vape']
            },
            'digighelioon': {
                #دیجی قلیون
                'name': 'Digi Ghelioon',
                'base_urls': ['https://digighelioon.com', 'http://digighelioon.com'],
                'category_selectors': [
                    'a.active',
                    '.menu-item a',
                    'nav a',
                    'a[href*="hookah-components"]',
                    'a[href*="category"]'
                ],
                'product_selectors': [
                    '.product',
                    '.product-item',
                    '.product-card',
                    '.goods-item'
                ],
                'name_selectors': [
                    '.product-name',
                    'h3',
                    'h2',
                    '.product-title'
                ],
                'price_selectors': [
                    '.woocommerce-Price-amount',
                    '.price',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    '.next',
                    '.pagination a',
                    'a[href*="page"]'
                ],
                'next_text': ['بعدی', 'next', '→'],
                'category_keywords': ['product-category', 'category', 'hookah-components']
            },
            'vape60': {
                #ویپ 60
                'name': 'Vape 60',
                'base_urls': ['https://vape60shop22.com', 'http://vape60shop22.com'],
                'category_selectors': [
                    '.menu-item a',
                    'nav a',
                    '.product-category a',
                    'a[href*="category"]'
                ],
                'product_selectors': [
                    '.product',
                    '.product-item',
                    '.woocommerce-product',
                    '.goods-item'
                ],
                'name_selectors': [
                    '.woocommerce-loop-product__title',
                    'h2',
                    'h3',
                    'b'
                ],
                'price_selectors': [
                    '.woocommerce-Price-amount',
                    '.price',
                    '.amount',
                    'bdi'
                ],
                'pagination_selectors': [
                    '.next.page-numbers',
                    '.pagination a',
                    'a.next'
                ],
                'next_text': ['←', 'next', 'بعدی'],
                'category_keywords': ['product-category', 'category', 'podsystem']
            }
        }
    
    def identify_site(self, url):
        """شناسایی هوشمند سایت بر اساس URL و محتوا"""
        logging.info(f"🔍 شناسایی سایت برای: {url}")
        
        # شناسایی بر اساس URL
        for site_id, config in self.site_configs.items():
            for base_url in config['base_urls']:
                if base_url in url:
                    logging.info(f"✅ سایت شناسایی شد: {config['name']}")
                    return site_id
        
        # شناسایی بر اساس محتوای صفحه
        try:
            self.driver.get(url)
            time.sleep(3)
            page_source = self.driver.page_source
            title = self.driver.title.lower()
            
            if 'dokhan' in title or 'دخان' in page_source:
                return 'dokhanmarket'
            elif 'tajvape' in title or 'tajvape' in page_source:
                return 'tajvape'
            elif 'vapoursdaily' in title or 'vapours' in page_source:
                return 'vapoursdaily'
            elif 'smokcenter' in title or 'smok' in page_source:
                return 'smokcenter'
            elif 'digizima' in title or 'زیما' in page_source:
                return 'digizima'
            elif 'digighelioon' in title or 'قلیون' in page_source:
                return 'digighelioon'
            elif 'vape60' in title or 'vape60' in page_source:
                return 'vape60'
            else:
                logging.warning("⚠️ سایت ناشناخته، استفاده از پیکربندی عمومی")
                return 'tajvape'
                
        except Exception as e:
            logging.error(f"خطا در شناسایی سایت: {e}")
            return 'tajvape'
    
    def setup_logging(self):
        """تنظیمات سیستم گزارش‌دهی"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'tmp_jobs/{self.job_id}_log.txt', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def update_status(self, message, page=1, total_pages=1, products_found=0, current_site=""):
        """آپدیت وضعیت"""
        status = {
            'job_id': self.job_id,
            'status': message,
            'page': page,
            'total_pages': total_pages,
            'products_count': products_found,
            'total_products': len(self.products_data),
            'current_site': current_site,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(f'tmp_jobs/{self.job_id}_status.json', 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving status: {e}")
    
    def get_categories(self, url, site_id):
        """دریافت دسته‌بندی‌ها برای سایت مشخص"""
        self.update_status("دریافت دسته‌بندی‌ها", current_site=site_id)
        logging.info(f"🔍 دریافت دسته‌بندی‌ها از: {url} برای سایت {site_id}")
        
        try:
            self.driver.get(url)
            time.sleep(4)
            
            categories = []
            config = self.site_configs[site_id]
            seen_urls = set()
            
            # روش 1: استفاده از سلکتورهای مخصوص سایت
            for selector in config['category_selectors']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logging.info(f"🎯 {len(elements)} المنت با سلکتور {selector}")
                        
                        for element in elements:
                            try:
                                href = element.get_attribute('href')
                                text = element.text.strip()
                                
                                if href and href not in seen_urls and text and 2 < len(text) < 100:
                                    if self.is_valid_category(href, text, site_id):
                                        categories.append({
                                            'name': text,
                                            'url': href,
                                            'site': site_id,
                                            'site_name': config['name']
                                        })
                                        seen_urls.add(href)
                                        logging.info(f"📁 دسته‌بندی: {text}")
                            except Exception as e:
                                logging.debug(f"خطا در پردازش المنت: {e}")
                                continue
                        
                        if len(categories) >= 10:
                            break
                except Exception as e:
                    logging.debug(f"خطا در سلکتور {selector}: {e}")
                    continue
            
            # روش 2: جستجوی دستی در منوها
            if len(categories) < 3:
                categories.extend(self.find_categories_manually(site_id))
            
            # حذف موارد تکراری
            unique_categories = []
            seen_names = set()
            for cat in categories:
                if cat['name'] not in seen_names:
                    unique_categories.append(cat)
                    seen_names.add(cat['name'])
            
            if not unique_categories:
                unique_categories.append({
                    'name': 'محصولات اصلی',
                    'url': url,
                    'site': site_id,
                    'site_name': config['name']
                })
            
            logging.info(f"📂 {len(unique_categories)} دسته‌بندی برای {site_id} یافت شد")
            return unique_categories[:12]  # حداکثر 12 دسته‌بندی
            
        except Exception as e:
            logging.error(f"خطا در دریافت دسته‌بندی‌ها برای {site_id}: {e}")
            return [{
                'name': 'محصولات',
                'url': url,
                'site': site_id,
                'site_name': self.site_configs[site_id]['name']
            }]
    
    def find_categories_manually(self, site_id):
        """جستجوی دستی برای دسته‌بندی‌ها"""
        categories = []
        try:
            # جستجو در منوهای مختلف
            menu_selectors = ['nav', '.menu', '.navigation', '.main-menu', '.categories']
            
            for selector in menu_selectors:
                try:
                    menus = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for menu in menus:
                        links = menu.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            try:
                                href = link.get_attribute('href')
                                text = link.text.strip()
                                if href and text and len(text) > 2 and self.is_valid_category(href, text, site_id):
                                    categories.append({
                                        'name': text,
                                        'url': href,
                                        'site': site_id,
                                        'site_name': self.site_configs[site_id]['name']
                                    })
                            except:
                                continue
                except:
                    continue
        except:
            pass
        
        return categories
    
    def is_valid_category(self, href, text, site_id):
        """بررسی معتبر بودن دسته‌بندی"""
        if not href or not text:
            return False
        
        text_lower = text.lower()
        href_lower = href.lower()
        
        # کلمات ممنوعه
        exclude_words = [
            'home', 'main', 'صفحه اصلی', 'contact', 'تماس', 'about', 'درباره',
            'blog', 'بلاگ', 'account', 'حساب', 'cart', 'سبد', 'checkout', 'پرداخت',
            'search', 'جستجو', 'login', 'ورود', 'register', 'ثبت نام','اسموک سنتر TV'
        ]
        
        if any(word in text_lower for word in exclude_words):
            return False
        
        if any(word in href_lower for word in exclude_words):
            return False
        
        # فیلترهای خاص هر سایت
        config = self.site_configs[site_id]
        if any(keyword in href_lower for keyword in config['category_keywords']):
            return True
        
        # فیلتر عمومی
        category_indicators = ['category', 'cat', 'product', 'shop', 'محصول', 'دسته']
        if any(indicator in href_lower for indicator in category_indicators):
            return True
        
        return len(text) > 2 and len(text) < 50
    
    def scrape_category_pages(self, category_url, category_name, site_id):
        """اسکرپ تمام صفحات یک دسته‌بندی - **نسخه نهایی با کلیک**"""
        logging.info(f"🔄 شروع اسکرپ عمیق برای: {category_name}")
        
        all_products = []
        current_page = 1
        max_pages = 50
        consecutive_empty_pages = 0
        max_consecutive_empty = 1
        
        # بارگذاری صفحه اول
        self.driver.get(category_url)
        time.sleep(3)
        
        while current_page <= max_pages and self.is_running and consecutive_empty_pages < max_consecutive_empty:
            logging.info(f"📄 صفحه {current_page} از {category_name}")
            self.update_status(f"صفحه {current_page} از {category_name}", current_page, max_pages, len(all_products), site_id)
            
            try:
                # اسکرپ محصولات صفحه فعلی
                page_products = self.scrape_products_from_page(category_name, site_id)
                
                if page_products:
                    # فیلتر محصولات تکراری
                    new_products = []
                    for product in page_products:
                        if not any(p['name'] == product['name'] and p['price'] == product['price'] 
                                for p in all_products):
                            new_products.append(product)
                    
                    if new_products:
                        all_products.extend(new_products)
                        logging.info(f"✅ {len(new_products)} محصول جدید از صفحه {current_page}")
                        consecutive_empty_pages = 0  # ریست شمارنده
                    else:
                        logging.info(f"🔄 همه محصولات تکراری، صفحه {current_page}")
                        consecutive_empty_pages += 1
                else:
                    logging.warning(f"⚠️ هیچ محصولی در صفحه {current_page}")
                    consecutive_empty_pages += 1
                
                # اگر ۲ صفحه پشت سر هم خالی/تکراری بود، توقف کن
                if consecutive_empty_pages >= max_consecutive_empty:
                    logging.info(f"🚫 {max_consecutive_empty} صفحه پشت سر هم خالی - توقف")
                    break
                
                # سعی کن به صفحه بعد بری
                if current_page < max_pages:
                    if self.has_next_page_improved(site_id):
                        if self.click_next_page(site_id):
                            current_page += 1
                            time.sleep(2)
                        else:
                            # اگر نتوانست کلیک کنه، با URL مستقیم برو
                            logging.info("🔄 استفاده از URL مستقیم برای صفحه بعد")
                            next_url = self.get_page_url(category_url, current_page + 1, site_id)
                            self.driver.get(next_url)
                            time.sleep(3)
                            current_page += 1
                    else:
                        logging.info("🏁 صفحه بعدی وجود ندارد - اتمام دسته‌بندی")
                        break
                else:
                    logging.info("🏁 به حداکثر صفحات مجاز رسیدیم")
                    break
                    
            except Exception as e:
                logging.error(f"❌ خطا در صفحه {current_page}: {e}")
                consecutive_empty_pages += 1
                
                # سعی کن با URL مستقیم به صفحه بعد بری
                try:
                    next_url = self.get_page_url(category_url, current_page + 1, site_id)
                    self.driver.get(next_url)
                    time.sleep(3)
                    current_page += 1
                except:
                    break
        
        logging.info(f"🎉 اتمام {category_name}: {len(all_products)} محصول از {current_page} صفحه")
        return all_products
                
    def get_page_url(self, base_url, page_number, site_id):
        """ساخت URL صفحه - **پشتیبانی از تمام فرمت‌ها**"""
        if page_number == 1:
            return base_url
            
        # حذف پارامترهای صفحه‌بندی موجود
        base_clean = re.sub(r'[?&](page|paged)=\d+', '', base_url)
        base_clean = re.sub(r'/page/\d+', '', base_clean)
        base_clean = re.sub(r'/product-page/\d+', '', base_clean)
            
        # اضافه کردن صفحه جدید بر اساس نوع سایت
        if site_id in ['tajvape', 'vapoursdaily', 'digizima']:
            # فرمت: /page/2/
            return f"{base_clean}/page/{page_number}/"
        elif site_id in ['smokcenter', 'vape60']:
            # فرمت: ?page=2
            separator = '?' if '?' not in base_clean else '&'
            return f"{base_clean}{separator}page={page_number}"
        elif site_id in ['dokhanmarket', 'digighelioon']:
                # فرمت: /product-page/2/
            return f"{base_clean}/product-page/{page_number}/"
        else:
                # فرمت پیش‌فرض
            separator = '?' if '?' not in base_clean else '&'
            return f"{base_clean}{separator}page={page_number}"
        
    def has_next_page_improved(self, site_id):
        """بررسی وجود صفحه بعد - **نسخه فوق پیشرفته**"""
        config = self.site_configs[site_id]
        current_url = self.driver.current_url
        
        logging.info(f"🔍 جستجوی صفحه بعد برای {config['name']}")
        
        # روش 1: جستجو برای دکمه‌های "بعدی" با سلکتورهای مختلف
        next_selectors = [
            'a.next', '.next', '.pagination-next', 
            '.page-numbers.next', '.next.page-numbers',
            'a[rel="next"]', '.next-page', '.pagination .next',
            '.woocommerce-pagination .next', '.nav-next',
            'a:contains("بعدی")', 'a:contains("next")',
            'button.next', '.load-more', '.pagination-next a'
        ]
        
        for selector in next_selectors:
            try:
                next_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in next_elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.lower().strip()
                            href = element.get_attribute('href') or ''
                            
                            # کلمات کلیدی برای صفحه بعد
                            next_keywords = ['next', 'بعدی', '→', '»', '>', 'load more', 'more']
                            prev_keywords = ['قبلی', 'قبل', '←', '«', '<', 'previous']
                            
                            if (any(keyword in text for keyword in next_keywords) and 
                                not any(keyword in text for keyword in prev_keywords)):
                                logging.info(f"🎯 صفحه بعد پیدا شد با سلکتور: {selector}")
                                return True
                    except:
                        continue
            except:
                continue
        
        # روش 2: جستجو در کل صفحه برای لینک‌های صفحه‌بندی
        try:
            # تمام لینک‌های ممکن برای صفحه‌بندی
            all_links = self.driver.find_elements(By.CSS_SELECTOR, 
                'a[href*="page"], a[href*="paged"], [class*="page"], [class*="pagination"] a, .page-numbers a, .pagination a, .page-links a')
            
            current_page = self.get_current_page_number(current_url)
            
            for link in all_links:
                try:
                    if not link.is_displayed():
                        continue
                        
                    link_text = link.text.strip()
                    href = link.get_attribute('href')
                    
                    if not href:
                        continue
                    
                    # اگر لینک شماره صفحه بعد باشد
                    if link_text.isdigit():
                        link_page = int(link_text)
                        if link_page == current_page + 1:
                            logging.info(f"🔢 صفحه بعد پیدا شد: صفحه {link_page}")
                            return True
                    
                    # اگر لینک شامل کلمات صفحه بعد باشد
                    text_lower = link_text.lower()
                    if any(word in text_lower for word in ['next', 'بعدی', '→', '»', '>']):
                        if not any(word in text_lower for word in ['قبلی', 'قبل', '←']):
                            logging.info(f"📖 صفحه بعد با متن: {link_text}")
                            return True
                            
                except:
                    continue
        except Exception as e:
            logging.debug(f"خطا در جستجوی لینک‌ها: {e}")
        
        # روش 3: جستجو با XPath برای متن‌های خاص
        try:
            next_texts = ['بعدی', 'next', '→', '»', '>', 'Load more', 'More products']
            for text in next_texts:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                # بررسی که المنت واقعاً برای صفحه بعد است
                                parent = element.find_element(By.XPATH, './..')
                                if parent.tag_name == 'a' or parent.get_attribute('onclick'):
                                    logging.info(f"🔍 صفحه بعد با XPath: {text}")
                                    return True
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            logging.debug(f"خطا در جستجوی XPath: {e}")
        
        # روش 4: بررسی تغییر در URL بعد از کلیک (برای Load More)
        try:
            # پیدا کردن المنت‌هایی که ممکن است Load More باشند
            buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                'button, [onclick], [class*="load"], [class*="more"]')
            
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        text = button.text.lower()
                        if any(word in text for word in ['more', 'load', 'بارگیری', 'بیشتر']):
                            logging.info(f"🔄 دکمه Load More پیدا شد: {text}")
                            return True
                except:
                    continue
        except:
            pass
        
        logging.info("❌ هیچ صفحه بعدی یافت نشد")
        return False
    
    def click_next_page(self, site_id):
        """کلیک روی صفحه بعد - **تابع جدید**"""
        config = self.site_configs[site_id]
        current_url = self.driver.current_url
        
        logging.info("🖱️ تلاش برای کلیک روی صفحه بعد...")
        
        # روش 1: کلیک روی دکمه‌های "بعدی" با سلکتورهای مختلف
        next_selectors = [
            'a.next', '.next', '.pagination-next', 
            '.page-numbers.next', '.next.page-numbers',
            'a[rel="next"]', '.next-page', '.pagination .next',
            '.woocommerce-pagination .next', '.nav-next'
        ]
        
        for selector in next_selectors:
            try:
                next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in next_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            logging.info(f"✅ کلیک روی صفحه بعد با سلکتور: {selector}")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            return True
                    except Exception as e:
                        logging.debug(f"خطا در کلیک با سلکتور {selector}: {e}")
                        continue
            except Exception as e:
                logging.debug(f"خطا در پیدا کردن سلکتور {selector}: {e}")
                continue
        
        # روش 2: کلیک روی شماره صفحات بعدی
        try:
            current_page = self.get_current_page_number(current_url)
            page_links = self.driver.find_elements(By.CSS_SELECTOR, 
                '.page-numbers a, .pagination a, a.page-numbers, .page-links a')
            
            for link in page_links:
                try:
                    if link.is_displayed() and link.is_enabled():
                        link_text = link.text.strip()
                        if link_text.isdigit():
                            link_page = int(link_text)
                            if link_page == current_page + 1:
                                logging.info(f"🔢 کلیک روی صفحه {link_page}")
                                self.driver.execute_script("arguments[0].click();", link)
                                time.sleep(3)
                                return True
                except:
                    continue
        except Exception as e:
            logging.debug(f"خطا در کلیک روی شماره صفحات: {e}")
        
        # روش 3: کلیک با XPath روی متن‌های "بعدی"
        try:
            next_texts = ['بعدی', 'next', '→', '»', '>']
            for text in next_texts:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                # بررسی که المنت واقعاً برای صفحه بعد است
                                element_text = element.text.lower()
                                if not any(word in element_text for word in ['قبلی', 'قبل', '←', '«']):
                                    logging.info(f"📖 کلیک روی: {text}")
                                    self.driver.execute_script("arguments[0].click();", element)
                                    time.sleep(3)
                                    return True
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            logging.debug(f"خطا در کلیک XPath: {e}")
        
        # روش 4: کلیک روی دکمه‌های Load More
        try:
            load_more_selectors = [
                'button.load-more', '.load-more', '[class*="load-more"]',
                '.load-more-products', '.ajax-load-more',
                'button:contains("Load more")', 'button:contains("بارگیری بیشتر")'
            ]
            
            for selector in load_more_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                logging.info(f"🔄 کلیک روی Load More: {selector}")
                                self.driver.execute_script("arguments[0].click();", button)
                                time.sleep(4)  # زمان بیشتر برای لود محصولات جدید
                                return True
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            logging.debug(f"خطا در کلیک Load More: {e}")
        
        logging.warning("❌ نتوانست روی صفحه بعد کلیک کند")
        return False
        
    def get_current_page_number(self, url):
            """دریافت شماره صفحه فعلی از URL - **اصلاح شده**"""
            try:
                patterns = [
                    r'/page/(\d+)/',
                    r'[?&]page=(\d+)',
                    r'/product-page/(\d+)/',
                    r'[?&]paged=(\d+)',
                    r'/page-(\d+)/',
                    r'/page(\d+)/'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        page_num = int(match.group(1))
                        logging.info(f"📖 شماره صفحه فعلی: {page_num}")
                        return page_num
                
                # اگر شماره صفحه پیدا نشد، احتمالاً صفحه اول است
                return 1
            except:
                return 1
    
    def scrape_products_from_page(self, category_name, site_id):
        """اسکرپ محصولات با فیلتر تکراری"""
        products = []
        config = self.site_configs[site_id]
        
        for selector in config['product_selectors']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logging.info(f"🎯 {len(elements)} المنت با {selector}")
                    
                    for element in elements:
                        try:
                            if not self.is_running:
                                break
                                
                            product = self.extract_product_data(element, category_name, site_id)
                            if product and self.is_valid_product(product):
                                # بررسی تکراری نبودن در همین صفحه
                                if not any(p['name'] == product['name'] and p['price'] == product['price'] 
                                        for p in products):
                                    products.append(product)
                        except Exception as e:
                            continue
                    
                    if products:
                        break
            except:
                continue
        
        return products
    
    def is_duplicate_product(self, new_product, existing_products):
        """بررسی تکراری نبودن محصول"""
        for existing in existing_products:
            if (existing['name'] == new_product['name'] and 
                existing['price'] == new_product['price'] and
                existing['site'] == new_product['site']):
                return True
        return False
    
    def extract_product_data(self, element, category_name, site_id):
        """استخراج اطلاعات محصول - **اصلاح شده**"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 10:  # کاهش حداقل طول متن
                return None
            
            # استخراج نام
            name = self.extract_product_name(element, site_id)
            if not name or len(name) < 2:  # کاهش حداقل طول نام
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                name = lines[0] if lines else "محصول ناشناخته"
            
            # استخراج قیمت
            price = self.extract_product_price(element, site_id)
            if not price:
                price = self.extract_price_from_text(full_text)
            
            if not price:
                return None
            
            # استخراج URL
            url = self.extract_product_url(element, site_id)
            
            # استخراج SKU
            sku = self.extract_sku(element, full_text, site_id)
            
            product_data = {
                'name': name[:200],  # افزایش طول نام
                'price': price,
                'categories': category_name,
                'site': self.site_configs[site_id]['name'],
                'site_id': site_id,
                'type': 'product',
                'variation': 'standard',
                'sku': sku,
                'description': full_text[:300],  # افزایش طول توضیحات
                'url': url,
                'grouped_products': '',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return product_data
            
        except Exception as e:
            logging.debug(f"خطا در استخراج محصول: {e}")
            return None
    
    def extract_product_name(self, element, site_id):
        """استخراج نام محصول - **اصلاح شده**"""
        config = self.site_configs[site_id]
        
        for selector in config['name_selectors']:
            try:
                if selector in ['h2', 'h3', 'h4', 'b', 'strong']:
                    # اگر سلکتور تگ HTML است
                    if element.tag_name == selector:
                        name = element.text.strip()
                        if name and len(name) > 1:
                            return name
                    # یا پیدا کردن در فرزندان
                    try:
                        name_elems = element.find_elements(By.TAG_NAME, selector)
                        for name_elem in name_elems:
                            name = name_elem.text.strip()
                            if name and len(name) > 1:
                                return name
                    except:
                        continue
                else:
                    # سلکتور CSS معمولی
                    name_elems = element.find_elements(By.CSS_SELECTOR, selector)
                    for name_elem in name_elems:
                        name = name_elem.text.strip()
                        if name and len(name) > 1:
                            return name
            except:
                continue
        
        return None
    
    def extract_product_price(self, element, site_id):
        """استخراج قیمت محصول - **اصلاح شده**"""
        config = self.site_configs[site_id]
        
        for selector in config['price_selectors']:
            try:
                price_elems = element.find_elements(By.CSS_SELECTOR, selector)
                for price_elem in price_elems:
                    try:
                        price_text = price_elem.text.strip()
                        price = self.extract_price_from_text(price_text)
                        if price:
                            return price
                    except:
                        continue
            except:
                continue
        
        return None
    
    def extract_price_from_text(self, text):
        """استخراج قیمت از متن - **اصلاح شده**"""
        try:
            # پاک کردن متن و حفظ اعداد و جداکننده‌ها
            clean_text = re.sub(r'[^\d,\.\s]', '', text.strip())
            clean_text = re.sub(r'\s+', ' ', clean_text)
            
            # الگوهای مختلف قیمت
            patterns = [
                r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # فرمت 1,000,000
                r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)',  # فرمت 1.000.000
                r'(\d+)'  # فقط اعداد
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, clean_text)
                for match in matches:
                    try:
                        # حذف جداکننده‌ها و تبدیل به عدد
                        price_str = re.sub(r'[^\d]', '', match)
                        if price_str.isdigit():
                            price = int(price_str)
                            # محدوده منطقی قیمت برای محصولات ویپ
                            if 1000 <= price <= 50000000:
                                return str(price)
                    except:
                        continue
        except:
            pass
        
        return None
    
    def extract_product_url(self, element, site_id):
        """استخراج URL محصول"""
        try:
            # اگر خود المنت لینک است
            if element.tag_name == 'a':
                href = element.get_attribute('href')
                if href and 'http' in href:
                    return href
            
            # جستجو برای لینک در فرزندان
            links = element.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and 'http' in href:
                    return href
            
            return ""
        except:
            return ""
    
    def extract_sku(self, element, text, site_id):
        """استخراج SKU محصول"""
        try:
            sku_patterns = [
                r'SKU:\s*([A-Za-z0-9-]+)',
                r'کد:\s*([A-Za-z0-9-]+)',
                r'شناسه:\s*([A-Za-z0-9-]+)',
                r'([A-Z]{2,3}\d{3,})',
                r'کد محصول:\s*([^\s]+)'
            ]
            
            for pattern in sku_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0]
        except:
            pass
        
        return ""
    
    def is_valid_product(self, product):
        """بررسی معتبر بودن محصول - **اصلاح شده**"""
        if not product.get('name') or len(product['name']) < 2:
            return False
        
        if not product.get('price') or not product['price'].isdigit():
            return False
        
        price_num = int(product['price'])
        if price_num < 500 or price_num > 100000000:  # گسترش محدوده قیمت
            return False
        
        return True
    
    def alternative_scraping_methods(self, category_name, site_id):
        """روش‌های جایگزین برای اسکرپ - **اصلاح شده**"""
        products = []
        
        try:
            # جستجو برای المنت‌های حاوی قیمت
            price_indicators = ['تومان', 'ریال', 'price', 'قیمت', 'خرید']
            for indicator in price_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, f'//*[contains(text(), "{indicator}")]')
                    for element in elements[:50]:  # افزایش تعداد المنت‌ها
                        try:
                            # پیدا کردن والد که احتمالاً حاوی اطلاعات محصول است
                            parent = element.find_element(By.XPATH, './ancestor::*[position()<5]')
                            text = parent.text.strip()
                            if len(text) > 30 and self.looks_like_product(text):
                                product = self.create_product_from_text(text, category_name, site_id)
                                if product and self.is_valid_product(product) and not self.is_duplicate_product(product, products):
                                    products.append(product)
                        except:
                            continue
                except:
                    continue
        except:
            pass
        
        return products
    
    def create_product_from_text(self, text, category_name, site_id):
        """ایجاد محصول از متن"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 2]
            if not lines:
                return None
            
            # پیدا کردن نام (اولین خط معقول)
            name = lines[0]
            for line in lines:
                if len(line) > 5 and not any(indicator in line.lower() for indicator in ['تومان', 'ریال', 'قیمت', 'price', 'خرید']):
                    name = line
                    break
            
            # استخراج قیمت
            price = self.extract_price_from_text(text)
            if not price:
                return None
            
            return {
                'name': name[:200],
                'price': price,
                'categories': category_name,
                'site': self.site_configs[site_id]['name'],
                'site_id': site_id,
                'type': 'product',
                'variation': 'standard',
                'sku': '',
                'description': text[:300],
                'url': '',
                'grouped_products': '',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except:
            return None
    
    def looks_like_product(self, text):
        """بررسی اینکه متن شبیه محصول است - **اصلاح شده**"""
        must_have = ['تومان', 'ریال', 'price']
        nice_to_have = ['قیمت', 'خرید', 'جویس', 'پاد', 'ویپ', 'کویل', 'سیستم', 'محصول', 'product', 'vape']
        
        text_lower = text.lower()
        
        if not any(indicator in text_lower for indicator in must_have):
            return False
        
        if any(indicator in text_lower for indicator in nice_to_have):
            return True
        
        return len(text) > 50  # کاهش حداقل طول
    
    def scrape_all_sites(self):
        """اسکرپ تمام 7 سایت هدف"""
        target_sites = [
            "https://vape60shop22.com",
            "https://tajvape12.com", 
            "https://vapoursdaily14.com",
            "https://digizima19.com",
            "https://smokcenter16.com",
            "https://digighelioon.com",
            "https://dokhanmarket3.com"
        ]
        
        return self.scrape_multiple_sites(target_sites)
    
    def scrape_multiple_sites(self, site_urls):
        """اسکرپ چندین سایت - **اصلاح نهایی**"""
        self.is_running = True
        total_results = []
        
        try:
            for i, site_url in enumerate(site_urls, 1):
                if not self.is_running:
                    break
                
                logging.info(f"🌐 شروع اسکرپ سایت {i}/{len(site_urls)}: {site_url}")
                self.update_status(f"سایت {i}", current_site=site_url)
                
                # شناسایی سایت
                site_id = self.identify_site(site_url)
                self.current_site = site_id
                
                # دریافت دسته‌بندی‌ها
                categories = self.get_categories(site_url, site_id)
                logging.info(f"📂 {len(categories)} دسته‌بندی برای {site_id} یافت شد")
                
                site_products = []
                
                # اسکرپ هر دسته‌بندی
                for j, category in enumerate(categories, 1):
                    if not self.is_running:
                        break
                    
                    logging.info(f"🔄 دسته‌بندی {j}/{len(categories)}: {category['name']}")
                    
                    # **اصلاح اصلی: برگشت به صفحه اصلی قبل از هر دسته‌بندی جدید**
                    try:
                        self.driver.get(site_url)  # برگشت به صفحه اصلی
                        time.sleep(2)
                    except:
                        pass
                    
                    # اسکرپ تمام صفحات این دسته‌بندی
                    category_products = self.scrape_category_pages(
                        category['url'], 
                        category['name'], 
                        site_id
                    )
                    
                    if category_products:
                        site_products.extend(category_products)
                        logging.info(f"✅ {len(category_products)} محصول از {category['name']}")
                    
                    time.sleep(2)  # تاخیر بین دسته‌بندی‌ها
                    
                    # **ذخیره موقت بعد از هر دسته‌بندی**
                    self.products_data.extend(site_products)
                    self.save_progress()
                    
                    # **آپدیت وضعیت برای نشان دادن پیشرفت**
                    self.update_status(
                        f"دسته‌بندی {j}/{len(categories)} از سایت {i}", 
                        current_site=site_id
                    )
                
                # **ذخیره نهایی محصولات این سایت**
                if site_products:
                    total_results.append({
                        'site': site_id,
                        'site_name': self.site_configs[site_id]['name'],
                        'url': site_url,
                        'categories_count': len(categories),
                        'products_count': len(site_products),
                        'status': 'success'
                    })
                    
                    logging.info(f"✅ اتمام سایت {site_id}: {len(site_products)} محصول")
                else:
                    logging.warning(f"⚠️ هیچ محصولی از سایت {site_id} یافت نشد")
                
                time.sleep(3)  # تاخیر بین سایت‌ها
            
            # **ذخیره نهایی همه محصولات**
            excel_file = self.save_to_excel()
            
            final_result = {
                'success': True,
                'job_id': self.job_id,
                'total_products': len(self.products_data),
                'sites_scraped': len(total_results),
                'excel_file': excel_file,
                'site_results': total_results,
                'message': f'تعداد {len(self.products_data)} محصول از {len(total_results)} سایت یافت شد'
            }
            
            logging.info(f"🎉 اتمام کامل اسکرپ: {final_result}")
            return final_result
            
        except Exception as e:
            error_msg = f"خطا: {str(e)}"
            logging.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'job_id': self.job_id
            }
        finally:
            self.is_running = False
    
    def save_progress(self):
        """ذخیره پیشرفت"""
        try:
            progress_data = {
                'job_id': self.job_id,
                'products': self.products_data,
                'total_products': len(self.products_data),
                'current_site': self.current_site,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(f'tmp_jobs/{self.job_id}.json', 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"خطا در ذخیره پیشرفت: {e}")
    
    def save_to_excel(self):
        """ذخیره در اکسل با حذف موارد تکراری - **نسخه نهایی**"""
        if not self.products_data:
            logging.warning("⚠️ هیچ داده‌ای برای ذخیره وجود ندارد")
            return None
        
        try:
            filename = f"tmp_jobs/{self.job_id}.xlsx"
            
            # ایجاد DataFrame از داده‌ها
            df = pd.DataFrame(self.products_data)
            
            # **حذف موارد تکراری قبل از ذخیره**
            initial_count = len(df)
            
            # حذف تکراری‌ها بر اساس نام، قیمت و سایت
            df = df.drop_duplicates(
                subset=['name', 'price', 'site'], 
                keep='first'
            )
            
            # همچنین حذف تکراری‌های دقیق (همه فیلدها)
            df = df.drop_duplicates(keep='first')
            
            final_count = len(df)
            duplicates_removed = initial_count - final_count
            
            logging.info(f"🧹 حذف {duplicates_removed} مورد تکراری از {initial_count} محصول")
            
            # اگر همه داده‌ها تکراری بودند
            if len(df) == 0:
                logging.warning("⚠️ همه داده‌ها تکراری بودند - ذخیره حداقل یک رکورد")
                # حداقل یک رکورد از داده اصلی نگه دار
                df = pd.DataFrame(self.products_data[:1])
            
            # ایجاد فایل اکسل با فرمت‌بندی
            wb = Workbook()
            ws = wb.active
            ws.title = "Products"
            
            # اضافه کردن هدرها
            headers = list(df.columns)
            ws.append(headers)
            
            # اضافه کردن داده‌های غیرتکراری
            for _, row in df.iterrows():
                ws.append(row.tolist())
            
            # اضافه کردن اطلاعات آماری در یک sheet جداگانه
            stats_sheet = wb.create_sheet(title="آمار")
            stats_data = [
                ["آمار محصولات استخراج شده"],
                ["تاریخ استخراج", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ["تعداد کل محصولات پیدا شده", initial_count],
                ["تعداد محصولات منحصر به فرد", final_count],
                ["تعداد موارد تکراری حذف شده", duplicates_removed],
                ["تعداد سایت‌ها", len(df['site'].unique())],
                [],
                ["تعداد محصولات هر سایت:"]
            ]
            
            # آمار هر سایت
            site_stats = df['site'].value_counts()
            for site, count in site_stats.items():
                stats_data.append([site, count])
            
            for row in stats_data:
                stats_sheet.append(row)
            
            # فرمت‌بندی
            self.apply_excel_styling(ws, len(df))
            
            # فرمت‌بندی sheet آمار
            try:
                for col in range(1, 3):
                    stats_sheet.column_dimensions[get_column_letter(col)].width = 30
                
                for row in range(1, len(stats_data) + 1):
                    for col in range(1, 3):
                        cell = stats_sheet.cell(row=row, column=col)
                        if row == 1:
                            cell.font = Font(bold=True, size=14, color="1565C0")
                        elif row <= 7:
                            cell.font = Font(bold=True, color="2E7D32")
            except:
                pass
            
            # ذخیره فایل
            wb.save(filename)
            logging.info(f"💾 فایل اکسل ذخیره شد: {filename} (با {final_count} محصول منحصر به فرد)")
            
            # همچنین یک فایل JSON با داده‌های غیرتکراری ذخیره کن
            unique_data = {
                'job_id': self.job_id,
                'total_products_initial': initial_count,
                'total_products_final': final_count,
                'duplicates_removed': duplicates_removed,
                'products': df.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(f'tmp_jobs/{self.job_id}_unique.json', 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)
            
            return filename
            
        except Exception as e:
            logging.error(f"❌ خطا در ذخیره اکسل: {e}")
            # ذخیره ساده در صورت خطا
            try:
                simple_filename = f"tmp_jobs/{self.job_id}_simple.xlsx"
                df = pd.DataFrame(self.products_data)
                df.to_excel(simple_filename, index=False, engine='openpyxl')
                return simple_filename
            except Exception as e2:
                logging.error(f"❌ خطا در ذخیره ساده: {e2}")
                return None
    
    def apply_excel_styling(self, worksheet, data_count):
        """اعمال استایل‌های زیبا به اکسل"""
        try:
            # رنگ‌های ملایم و چشم‌نواز
            header_fill = PatternFill(start_color="18AAC4", end_color="18AAC4", fill_type="solid")  # آبی بسیار ملایم
            even_row_fill = PatternFill(start_color="C2F0FF", end_color="C2F0FF", fill_type="solid")  # خاکستری بسیار ملایم
            odd_row_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")   # سفید
            price_fill = PatternFill(start_color="F0F8EB", end_color="F0F8EB", fill_type="solid")     # سبز بسیار ملایم
            site_fill = PatternFill(start_color="F0F8EB", end_color="F0F8EB", fill_type="solid")      # نارنجی بسیار ملایم
            
            # فونت‌ها
            header_font = Font(bold=True, color="2E4057", size=11)
            normal_font = Font(color="2D2D2D", size=10)
            price_font = Font(bold=True, color="2E8B57", size=10)
            site_font = Font(bold=True, color="2E4057", size=10)
            
            # تراز
            center_align = Alignment(horizontal='center', vertical='center')
            right_align = Alignment(horizontal='right', vertical='center')
            left_align = Alignment(horizontal='left', vertical='center')
            
            # فرمت‌بندی هدر
            for col in range(1, len(worksheet[1]) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_align
            
            # فرمت‌بندی داده‌ها
            for row in range(2, data_count + 2):
                # رنگ‌آمیزی سطرها یکی در میان
                if row % 2 == 0:
                    row_fill = even_row_fill
                else:
                    row_fill = odd_row_fill
                
                for col in range(1, len(worksheet[1]) + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.font = normal_font
                    cell.fill = row_fill
                    
                    header_value = worksheet.cell(row=1, column=col).value
                    
                    # فرمت مخصوص قیمت
                    if header_value == 'price':
                        cell.font = price_font
                        cell.fill = price_fill
                        cell.alignment = right_align
                    # فرمت مخصوص سایت
                    elif header_value in ['site', 'site_id']:
                        cell.font = site_font
                        cell.fill = site_fill
                        cell.alignment = center_align
                    # فرمت مخصوص نام
                    elif header_value == 'name':
                        cell.alignment = left_align
                    else:
                        cell.alignment = right_align
            
            # تنظیم عرض ستون‌ها
            column_widths = {
                'name': 80,
                'price': 15,
                'categories': 25,
                'site': 20,
                'site_id': 15,
                'description': 130,
                'url': 50
            }
            
            for col in range(1, len(worksheet[1]) + 1):
                header = worksheet.cell(row=1, column=col).value
                if header in column_widths:
                    worksheet.column_dimensions[get_column_letter(col)].width = column_widths[header]
                else:
                    worksheet.column_dimensions[get_column_letter(col)].width = 15
            
            # فریز کردن هدر
            worksheet.freeze_panes = "A2"
            
            logging.info("🎨 فرمت‌بندی اکسل اعمال شد")
            
        except Exception as e:
            logging.warning(f"خطا در اعمال استایل‌ها: {e}")
    
    def stop(self):
        """توقف اسکرپ"""
        self.is_running = False
    
    def close(self):
        """بستن درایور"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("🔚 درایور بسته شد")
            except:
                pass

# تابع اصلی برای اجرا
def main():
    """تابع اصلی برای اجرای اسکرپر"""
    scraper = AdvancedVapeScraper()
    
    try:
        result = scraper.scrape_all_sites()
        print("نتایج:", result)
        
        if result['success']:
            print(f"🎉 اسکرپ با موفقیت انجام شد!")
            print(f"📊 تعداد محصولات: {result['total_products']}")
            print(f"🌐 تعداد سایت‌ها: {result['sites_scraped']}")
            print(f"💾 فایل اکسل: {result['excel_file']}")
        else:
            print(f"❌ خطا: {result['error']}")
            
    except Exception as e:
        print(f"خطا در اجرای اصلی: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()