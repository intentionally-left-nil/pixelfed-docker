#! /bin/sh

set -x
# Create the symbolic link at runtime, once the app-storage volume has been mounted
ln -s /var/www/storage/app/public /var/www/public/storage || true
