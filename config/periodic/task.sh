#! /bin/sh
set -x
{
  /usr/local/bin/php /var/www/artisan schedule:run
} 1>/proc/1/fd/1 2>/proc/1/fd/2
