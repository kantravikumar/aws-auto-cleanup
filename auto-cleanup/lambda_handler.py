import boto3
import logging
import os
import sys

# enable logging
root = logging.getLogger()

if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.basicConfig(format="[%(levelname)s] %(message)s (%(filename)s, %(funcName)s(), line %(lineno)d)", level=os.environ.get('LOGLEVEL', 'WARNING').upper())

class Lambda:
    def __init__(self, helper, whitelist, settings, tree, region):
        self.helper = helper
        self.whitelist = whitelist
        self.settings = settings
        self.tree = tree
        self.region = region
        
        self.dry_run = settings.get('general', {}).get('dry_run', True)
        
        try:
            self.client = boto3.client('lambda', region_name=region)
        except:
            logging.critical(str(sys.exc_info()))
    
    
    def run(self):
        self.functions()
        self.layers()
        
    def functions(self):
        """
        Deletes Lambda Functions.
        """
        
        clean = self.settings.get('services').get('lambda', {}).get('functions', {}).get('clean', False)
        if clean:
            try:
                resources = self.client.list_functions().get('Functions')
            except:
                logging.critical(str(sys.exc_info()))
                return None
            
            ttl_days = self.settings.get('services').get('lambda', {}).get('functions', {}).get('ttl', 7)
            
            for resource in resources:
                try:
                    resource_id = resource.get('FunctionName')
                    resource_date = resource.get('LastModified')

                    if resource_id not in self.whitelist.get('lambda', {}).get('function', []):
                        delta = self.helper.get_day_delta(resource_date)
                    
                        if delta.days > ttl_days:
                            if not self.dry_run:
                                self.client.delete_function(FunctionName=resource_id)
                            
                            logging.info("Lambda Function '%s' was last modified %d days ago and has been deleted." % (resource_id, delta.days))
                        else:
                            logging.debug("Lambda Function '%s' was last modified %d days ago (less than TTL setting) and has not been deleted." % (resource_id, delta.days))
                    else:
                        logging.debug("Lambda Function '%s' has been whitelisted and has not been deleted." % (resource_id))
                except:
                    logging.critical(str(sys.exc_info()))
                
                self.tree.get('AWS').setdefault(
                    self.region, {}).setdefault(
                        'Lambda', {}).setdefault(
                            'Functions', []).append(resource_id)
        else:
            logging.debug("Skipping cleanup of Lambda Functions.")
    
    
    def layers(self):
        pass