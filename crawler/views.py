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
    """Home"""
    return render(request, 'crawler/index.html')

@csrf_exempt
def start_scraping(request):
    """Start scraping for multiple sites"""
    if request.method == 'POST':
        try:
            # Get JSON data from the request
            data = json.loads(request.body)
            sites = data.get('sites', [])
            
            if not sites:
                return JsonResponse({'success': False, 'error': 'Site not specified'})
            
            print(f"🔧 Start scraping for{len(sites)} Site: {sites}")
            
            # Create a new scraper
            scraper = AdvancedVapeScraper()
            
            # Run in a separate function
            def run_scraping():
                try:
                    # Use the new function for multisite scraping
                    result = scraper.scrape_multiple_sites(sites)
                    scraper.close()
                    print(f"✅ Scrape result: {result}")
                except Exception as e:
                    print(f"❌ Error in scrape: {e}")
            
            # Run in a new thread
            thread = threading.Thread(target=run_scraping)
            thread.daemon = True
            thread.start()
            
            # Reply immediately
            return JsonResponse({
                'success': True, 
                'message': f'Scrap for{len(sites)} The site has started',
                'job_id': scraper.job_id,
                'sites_count': len(sites)
            })
            
        except Exception as e:
            print(f"❌Error starting scrape: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def start_scraping_all(request):
    """Start scraping for all 7 sites automatically"""
    if request.method == 'POST':
        try:
            print("🔧 Start automatic scraping for all 7 sites")
            
            #Create a new scraper
            scraper = AdvancedVapeScraper()
            
            # Create a new scraper
            def run_scraping():
                try:
                    # Using the new function to scrape entire sites
                    result = scraper.scrape_all_sites()
                    scraper.close()
                    print(f"✅ Scrape result: {result}")
                except Exception as e:
                    print(f"❌ Error in scrape: {e}")
            
            # Run in a new thread
            thread = threading.Thread(target=run_scraping)
            thread.daemon = True
            thread.start()
            
            # Reply immediately
            return JsonResponse({
                'success': True, 
                'message': 'Automatic scraping started for 7 sites',
                'job_id': scraper.job_id,
                'sites_count': 7
            })
            
        except Exception as e:
            print(f"❌Error starting scrape: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def get_progress(request):
    """Get progress status"""
    try:
        # Find the latest status file
        if not os.path.exists('tmp_jobs'):
            return JsonResponse({
                'status': 'ready',
                'page': 0,
                'total_pages': 0,
                'products_count': 0,
                'total_products': 0,
                'current_site': ''
            })
            
        status_files = [f for f in os.listdir('tmp_jobs') if f.endswith('_status.json')]
        if status_files:
            #Find the newest file
            latest_file = max(status_files, key=lambda f: os.path.getctime(os.path.join('tmp_jobs', f)))
            with open(f'tmp_jobs/{latest_file}', 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                return JsonResponse(status_data)
        
        return JsonResponse({
            'status': 'Preparing...',
            'page': 0,
            'total_pages': 0,
            'products_count': 0,
            'total_products': 0,
            'current_site': ''
        })
        
    except Exception as e:
        return JsonResponse({
            'status': f'error: {str(e)}',
            'products_count': 0,
            'total_products': 0,
            'current_site': ''
        })

def preview_products(request, job_id):
    """Product Preview"""
    try:
        json_file = f'tmp_jobs/{job_id}.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', [])[:20]  # Only the first 20 products
            
            #Grouping products by site
            products_by_site = {}
            for product in products:
                site = product.get('site', 'uncertain')
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
                'error': 'No data found',
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
    """Download Excel File"""
    try:
        excel_file = f'tmp_jobs/{job_id}.xlsx'
        if os.path.exists(excel_file):
            # Read Excel file and send for download
            with open(excel_file, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="products_{job_id}.xlsx"'
                return response
        else:
            return JsonResponse({'success': False, 'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def test_view(request):
    """Test page to check server health"""
    return JsonResponse({
        'status': 'OK', 
        'message': 'The server is working',
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
    """Get the status of a specific job"""
    try:
        status_file = f'tmp_jobs/{job_id}_status.json'
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                return JsonResponse(status_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Job not found',
                'job_id': job_id
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'job_id': job_id
        }, status=500)

def list_jobs(request):
    """List of all available jobs"""
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
                        
                        # Calculate the number of scraped sites
                        sites_count = 0
                        json_file = f'tmp_jobs/{job_id}.json'
                        if os.path.exists(json_file):
                            with open(json_file, 'r', encoding='utf-8') as f2:
                                json_data = json.load(f2)
                                products = json_data.get('products', [])
                                # Number of unique sites
                                sites_count = len(set(p.get('site', '') for p in products if p.get('site')))
                        
                        jobs.append({
                            'job_id': job_id,
                            'status': status_data.get('status', 'uncertain'),
                            'products_count': status_data.get('total_products', 0),
                            'sites_count': sites_count,
                            'current_site': status_data.get('current_site', ''),
                            'timestamp': status_data.get('timestamp', '')
                        })
                except Exception as e:
                    print(f"Error processing the file{filename}: {e}")
                    continue
        
        # Sort by time (newest first)
        jobs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return JsonResponse({'jobs': jobs})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_site_statistics(request, job_id):
    """Product statistics by site"""
    try:
        json_file = f'tmp_jobs/{job_id}.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', [])
            
            # Statistics by site
            site_stats = {}
            for product in products:
                site = product.get('site', 'uncertain')
                if site not in site_stats:
                    site_stats[site] = {
                        'count': 0,
                        'total_price': 0,
                        'min_price': float('inf'),
                        'max_price': 0
                    }
                
                site_stats[site]['count'] += 1
                
                # Price calculation
                try:
                    price = int(product.get('price', 0))
                    site_stats[site]['total_price'] += price
                    site_stats[site]['min_price'] = min(site_stats[site]['min_price'], price)
                    site_stats[site]['max_price'] = max(site_stats[site]['max_price'], price)
                except:
                    pass
            
            # Calculate the average
            for site in site_stats:
                if site_stats[site]['count'] > 0:
                    site_stats[site]['avg_price'] = site_stats[site]['total_price'] // site_stats[site]['count']
                else:
                    site_stats[site]['avg_price'] = 0
                
                # Clean up infinite values
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
                'error': 'Job file not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def stop_scraping(request, job_id):
    """Stopping a Running Job"""
    if request.method == 'POST':
        try:
            # Here you need to create a mechanism to stop the scraper
            # For now, we're just updating the status
            status_file = f'tmp_jobs/{job_id}_status.json'
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                
                status_data['status'] = 'Stopped by user'
                status_data['stopped'] = True
                
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, ensure_ascii=False, indent=2)
            
            return JsonResponse({
                'success': True,
                'message': 'Stop request sent',
                'job_id': job_id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def get_supported_sites(request):
    """Get list of supported sites"""
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