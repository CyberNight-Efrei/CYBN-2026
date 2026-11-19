FROM php:8.5-apache

# Production config: never show PHP errors to visitors.
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
    && printf '%s\n' \
        '<Directory /var/www/html>' \
        '    Options -Indexes' \
        '    AllowOverride None' \
        '</Directory>' \
        'ServerTokens Prod' \
        'ServerSignature Off' \
        > /etc/apache2/conf-enabled/chathazard.conf

COPY src/ /var/www/html/

RUN chown -R www-data:www-data /var/www/html

ENV FLAG="CYBN{Kn0wn_s33d_4nd_z3r0_3ntr0py}" \
    DB_PATH="/tmp/chathazard.db"

EXPOSE 80
