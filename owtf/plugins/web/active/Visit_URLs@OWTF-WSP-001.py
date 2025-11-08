"""
This plugin does not perform ANY test: The aim is to visit all URLs grabbed so far and build
the transaction log to feed data to other plugins
NOTE: This is an active plugin because it may visit URLs retrieved by vulnerability scanner spiders
which may be considered sensitive or include vulnerability probing
"""
import logging

from owtf.requester.base import requester
from owtf.managers.url import get_urls_to_visit
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Visit URLs found by other tools, some could be sensitive: need permission"


def run(PluginInfo):
    """
    Visit all unvisited URLs and create transaction logs.
    
    Args:
        PluginInfo: Dictionary containing plugin context and configuration
        
    Returns:
        HtmlString: Formatted HTML report of visited URLs
    """
    # Get all unvisited URLs from database
    urls = get_urls_to_visit()
    
    # Handle case where no URLs are available
    if not urls:
        message = "No new URLs to visit. All discovered URLs have been processed."
        logging.info(message)
        return plugin_helper.HtmlString(f"<p>{message}</p>")
    
    # Initialize counters and result tracking
    total_urls = len(urls)
    visited_successfully = []
    failed_visits = []
    
    logging.info(f"Starting URL visit process: {total_urls} URLs to visit")
    
    # Visit each URL with error handling
    for idx, url in enumerate(urls, start=1):
        try:
            # Log progress for debugging and monitoring
            logging.debug(f"[{idx}/{total_urls}] Attempting to visit: {url}")
            
            # Make the HTTP request (True = use cache if available)
            transaction = requester.get_transaction(True, url)
            
            # Record successful visit with details
            visited_successfully.append({
                'url': url,
                'status_code': transaction.status if hasattr(transaction, 'status') else 'N/A',
                'response_time': transaction.time_human if hasattr(transaction, 'time_human') else 'N/A'
            })
            
            logging.debug(f"[{idx}/{total_urls}] Successfully visited: {url}")
            
        except ConnectionError as e:
            # Handle network-related errors
            error_msg = f"Connection failed: {str(e)}"
            failed_visits.append({'url': url, 'error': error_msg})
            logging.error(f"[{idx}/{total_urls}] Connection error for {url}: {error_msg}")
            
        except TimeoutError as e:
            # Handle timeout errors
            error_msg = f"Request timeout: {str(e)}"
            failed_visits.append({'url': url, 'error': error_msg})
            logging.error(f"[{idx}/{total_urls}] Timeout error for {url}: {error_msg}")
            
        except Exception as e:
            # Catch-all for unexpected errors
            error_msg = f"Unexpected error: {str(e)}"
            failed_visits.append({'url': url, 'error': error_msg})
            logging.error(f"[{idx}/{total_urls}] Error visiting {url}: {error_msg}")
    
    # Log final summary
    success_count = len(visited_successfully)
    failure_count = len(failed_visits)
    logging.info(
        f"URL visit complete: {success_count}/{total_urls} successful, "
        f"{failure_count} failed"
    )
    
    # Generate HTML report
    html_content = generate_html_report(
        total_urls, 
        visited_successfully, 
        failed_visits
    )
    
    return plugin_helper.HtmlString(html_content)


def generate_html_report(total, successful, failed):
    """
    Generate a formatted HTML report of URL visits.
    
    Args:
        total: Total number of URLs attempted
        successful: List of successfully visited URLs with details
        failed: List of failed URL visits with error messages
        
    Returns:
        str: HTML formatted report
    """
    # Build the report header with summary statistics
    html = ['<div class="url-visit-report">']
    html.append('<h3>URL Visit Summary</h3>')
    html.append(f'<p><strong>Total URLs:</strong> {total}</p>')
    html.append(f'<p><strong>Successfully Visited:</strong> {len(successful)} '
                f'({len(successful)*100//total if total > 0 else 0}%)</p>')
    html.append(f'<p><strong>Failed:</strong> {len(failed)} '
                f'({len(failed)*100//total if total > 0 else 0}%)</p>')
    
    # Add successful visits table
    if successful:
        html.append('<h4>Successfully Visited URLs</h4>')
        html.append('<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">')
        html.append('<thead><tr>')
        html.append('<th style="background-color: #4CAF50; color: white;">URL</th>')
        html.append('<th style="background-color: #4CAF50; color: white;">Status Code</th>')
        html.append('<th style="background-color: #4CAF50; color: white;">Response Time</th>')
        html.append('</tr></thead><tbody>')
        
        for item in successful:
            html.append('<tr>')
            html.append(f'<td>{item["url"]}</td>')
            html.append(f'<td style="text-align: center;">{item["status_code"]}</td>')
            html.append(f'<td style="text-align: center;">{item["response_time"]}</td>')
            html.append('</tr>')
        
        html.append('</tbody></table>')
    
    # Add failed visits table
    if failed:
        html.append('<h4>Failed URL Visits</h4>')
        html.append('<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">')
        html.append('<thead><tr>')
        html.append('<th style="background-color: #f44336; color: white;">URL</th>')
        html.append('<th style="background-color: #f44336; color: white;">Error</th>')
        html.append('</tr></thead><tbody>')
        
        for item in failed:
            html.append('<tr>')
            html.append(f'<td>{item["url"]}</td>')
            html.append(f'<td>{item["error"]}</td>')
            html.append('</tr>')
        
        html.append('</tbody></table>')
    
    html.append('</div>')
    
    return ''.join(html)