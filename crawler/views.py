from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .scraper import AdvancedVapeScraper
import threading
import pandas as pd
from uuid import uuid4

def index(request):
    """صفحه اصلی"""
    return render(request, 'crawler/index.html')

@csrf_exempt
def start_scraping(request):
    """شروع اسکرپینگ برای چندین سایت"""
    if request.method == 'POST':
        try:
            # دریافت داده‌های JSON از درخواست
            data = json.loads(request.body)
            sites = data.get('sites', [])
            
            if not sites:
                return JsonResponse({'success': False, 'error': 'سایتی مشخص نشده'})
            
            print(f"🔧 شروع اسکرپ برای {len(sites)} سایت: {sites}")
            
            # ایجاد اسکرپر جدید
            scraper = AdvancedVapeScraper()
            
            # اجرا در تابع جداگانه
            def run_scraping():
                try:
                    # استفاده از تابع جدید برای اسکرپ چندسایتی
                    result = scraper.scrape_multiple_sites(sites)
                    scraper.close()
                    print(f"✅ نتیجه اسکرپ: {result}")
                except Exception as e:
                    print(f"❌ خطا در اسکرپ: {e}")
            
            # اجرا در thread جدید
            thread = threading.Thread(target=run_scraping)
            thread.daemon = True
            thread.start()
            
            # فوراً پاسخ بده
            return JsonResponse({
                'success': True, 
                'message': f'اسکرپ برای {len(sites)} سایت شروع شد',
                'job_id': scraper.job_id,
                'sites_count': len(sites)
            })
            
        except Exception as e:
            print(f"❌ خطا در شروع اسکرپ: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'متد غیرمجاز'})

@csrf_exempt
def start_scraping_all(request):
    """شروع اسکرپینگ برای تمام 7 سایت به طور خودکار"""
    if request.method == 'POST':
        try:
            print("🔧 شروع اسکرپ خودکار برای تمام 7 سایت")
            
            # ایجاد اسکرپر جدید
            scraper = AdvancedVapeScraper()
            
            # اجرا در تابع جداگانه
            def run_scraping():
                try:
                    # استفاده از تابع جدید برای اسکرپ تمام سایت‌ها
                    result = scraper.scrape_all_sites()
                    scraper.close()
                    print(f"✅ نتیجه اسکرپ: {result}")
                except Exception as e:
                    print(f"❌ خطا در اسکرپ: {e}")
            
            # اجرا در thread جدید
            thread = threading.Thread(target=run_scraping)
            thread.daemon = True
            thread.start()
            
            # فوراً پاسخ بده
            return JsonResponse({
                'success': True, 
                'message': 'اسکرپ خودکار برای 7 سایت شروع شد',
                'job_id': scraper.job_id,
                'sites_count': 7
            })
            
        except Exception as e:
            print(f"❌ خطا در شروع اسکرپ: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'متد غیرمجاز'})

def get_progress(request):
    """دریافت وضعیت پیشرفت"""
    try:
        # پیدا کردن آخرین فایل وضعیت
        if not os.path.exists('tmp_jobs'):
            return JsonResponse({
                'status': 'آماده',
                'page': 0,
                'total_pages': 0,
                'products_count': 0,
                'total_products': 0,
                'current_site': ''
            })
            
        status_files = [f for f in os.listdir('tmp_jobs') if f.endswith('_status.json')]
        if status_files:
            # پیدا کردن جدیدترین فایل
            latest_file = max(status_files, key=lambda f: os.path.getctime(os.path.join('tmp_jobs', f)))
            with open(f'tmp_jobs/{latest_file}', 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                return JsonResponse(status_data)
        
        return JsonResponse({
            'status': 'در حال آماده سازی...',
            'page': 0,
            'total_pages': 0,
            'products_count': 0,
            'total_products': 0,
            'current_site': ''
        })
        
    except Exception as e:
        return JsonResponse({
            'status': f'خطا: {str(e)}',
            'products_count': 0,
            'total_products': 0,
            'current_site': ''
        })

def preview_products(request, job_id):
    """پیش‌نمایش محصولات"""
    try:
        json_file = f'tmp_jobs/{job_id}.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', [])[:20]  # فقط 20 محصول اول
            
            # گروه‌بندی محصولات بر اساس سایت
            products_by_site = {}
            for product in products:
                site = product.get('site', 'نامشخص')
                if site not in products_by_site:
                    products_by_site[site] = []
                products_by_site[site].append(product)
            
            return render(request, 'crawler/preview.html', {
                'products': products,
                'products_by_site': products_by_site,
                'job_id': job_id,
                'total_products': len(data.get('products', [])),
                'sites_count': len(products_by_site)
            })
        else:
            return render(request, 'crawler/preview.html', {
                'error': 'داده‌ای یافت نشد',
                'products': [],
                'products_by_site': {},
                'total_products': 0,
                'sites_count': 0
            })
    except Exception as e:
        return render(request, 'crawler/preview.html', {
            'error': str(e),
            'products': [],
            'products_by_site': {},
            'total_products': 0,
            'sites_count': 0
        })

def download_excel(request, job_id):
    """دانلود فایل اکسل"""
    try:
        excel_file = f'tmp_jobs/{job_id}.xlsx'
        if os.path.exists(excel_file):
            # خواندن فایل اکسل و ارسال برای دانلود
            with open(excel_file, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="products_{job_id}.xlsx"'
                return response
        else:
            return JsonResponse({'success': False, 'error': 'فایل یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def test_view(request):
    """صفحه تست برای بررسی سلامت سرور"""
    return JsonResponse({
        'status': 'OK', 
        'message': 'سرور کار می‌کند',
        'endpoints': {
            'home': '/',
            'test': '/test/',
            'start_scraping': '/start-scraping/',
            'start_scraping_all': '/start-scraping-all/',
            'progress': '/progress/',
            'preview': '/preview/<job_id>/',
            'download': '/download/<job_id>/',
            'job_status': '/job-status/<job_id>/',
            'list_jobs': '/list-jobs/'
        },
        'supported_sites': [
            'Vape60shop22.com',
            'Tajvape12.com', 
            'Vapoursdaily14.com',
            'Digizima19.com',
            'Smokcenter16.com',
            'Digighelioon.com',
            'Dokhanmarket3.com'
        ]
    })

def get_job_status(request, job_id):
    """دریافت وضعیت یک Job خاص"""
    try:
        status_file = f'tmp_jobs/{job_id}_status.json'
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                return JsonResponse(status_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Job یافت نشد',
                'job_id': job_id
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'job_id': job_id
        }, status=500)

def list_jobs(request):
    """لیست تمام Jobهای موجود"""
    try:
        if not os.path.exists('tmp_jobs'):
            return JsonResponse({'jobs': []})
        
        jobs = []
        for filename in os.listdir('tmp_jobs'):
            if filename.endswith('_status.json'):
                job_id = filename.replace('_status.json', '')
                try:
                    with open(f'tmp_jobs/{filename}', 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                        
                        # محاسبه تعداد سایت‌های اسکرپ شده
                        sites_count = 0
                        json_file = f'tmp_jobs/{job_id}.json'
                        if os.path.exists(json_file):
                            with open(json_file, 'r', encoding='utf-8') as f2:
                                json_data = json.load(f2)
                                products = json_data.get('products', [])
                                # تعداد سایت‌های منحصر به فرد
                                sites_count = len(set(p.get('site', '') for p in products if p.get('site')))
                        
                        jobs.append({
                            'job_id': job_id,
                            'status': status_data.get('status', 'نامشخص'),
                            'products_count': status_data.get('total_products', 0),
                            'sites_count': sites_count,
                            'current_site': status_data.get('current_site', ''),
                            'timestamp': status_data.get('timestamp', '')
                        })
                except Exception as e:
                    print(f"خطا در پردازش فایل {filename}: {e}")
                    continue
        
        # مرتب‌سازی بر اساس زمان (جدیدترین اول)
        jobs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return JsonResponse({'jobs': jobs})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_site_statistics(request, job_id):
    """آمار محصولات بر اساس سایت"""
    try:
        json_file = f'tmp_jobs/{job_id}.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', [])
            
            # آمار بر اساس سایت
            site_stats = {}
            for product in products:
                site = product.get('site', 'نامشخص')
                if site not in site_stats:
                    site_stats[site] = {
                        'count': 0,
                        'total_price': 0,
                        'min_price': float('inf'),
                        'max_price': 0
                    }
                
                site_stats[site]['count'] += 1
                
                # محاسبه قیمت
                try:
                    price = int(product.get('price', 0))
                    site_stats[site]['total_price'] += price
                    site_stats[site]['min_price'] = min(site_stats[site]['min_price'], price)
                    site_stats[site]['max_price'] = max(site_stats[site]['max_price'], price)
                except:
                    pass
            
            # محاسبه میانگین
            for site in site_stats:
                if site_stats[site]['count'] > 0:
                    site_stats[site]['avg_price'] = site_stats[site]['total_price'] // site_stats[site]['count']
                else:
                    site_stats[site]['avg_price'] = 0
                
                # تمیز کردن مقادیر بی‌نهایت
                if site_stats[site]['min_price'] == float('inf'):
                    site_stats[site]['min_price'] = 0
            
            return JsonResponse({
                'success': True,
                'job_id': job_id,
                'total_products': len(products),
                'total_sites': len(site_stats),
                'site_statistics': site_stats
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'فایل Job یافت نشد'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def stop_scraping(request, job_id):
    """توقف یک Job در حال اجرا"""
    if request.method == 'POST':
        try:
            # اینجا باید مکانیزمی برای توقف اسکرپر ایجاد کنید
            # در حال حاضر، فقط وضعیت را آپدیت می‌کنیم
            status_file = f'tmp_jobs/{job_id}_status.json'
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                
                status_data['status'] = 'متوقف شده توسط کاربر'
                status_data['stopped'] = True
                
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, ensure_ascii=False, indent=2)
            
            return JsonResponse({
                'success': True,
                'message': 'درخواست توقف ارسال شد',
                'job_id': job_id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'متد غیرمجاز'})

def get_supported_sites(request):
    """دریافت لیست سایت‌های پشتیبانی شده"""
    supported_sites = [
        {
            'name': 'Vape 60 Shop',
            'url': 'https://vape60shop22.com',
            'id': 'vape60'
        },
        {
            'name': 'Tajvape',
            'url': 'https://tajvape12.com',
            'id': 'tajvape'
        },
        {
            'name': 'Vapours Daily',
            'url': 'https://vapoursdaily14.com',
            'id': 'vapoursdaily'
        },
        {
            'name': 'Digi Zima',
            'url': 'https://digizima19.com',
            'id': 'digizima'
        },
        {
            'name': 'Smok Center',
            'url': 'https://smokcenter16.com',
            'id': 'smokcenter'
        },
        {
            'name': 'Digi Ghelioon',
            'url': 'https://digighelioon.com',
            'id': 'digighelioon'
        },
        {
            'name': 'Dokhan Market',
            'url': 'https://dokhanmarket3.com',
            'id': 'dokhanmarket'
        }
    ]
    
    return JsonResponse({
        'success': True,
        'sites': supported_sites,
        'total_sites': len(supported_sites)
    })