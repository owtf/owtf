#!/usr/bin/env sh
# This script is a helper for starting the postgres server if service or systemctl fail

# Bail out if not root privileges
if [ "$(id -u)" != "0" ]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

postgres_version="$(psql --version 2>&1 | tail -1 | awk '{print $3}' | sed 's/\./ /g' | awk '{print $1 "." $2}')"

PGUSER=postgres
PGVAR="/var/lib/postgres"
if [ ! -d "$PGVAR" ]; then
  PGVAR="/var/lib/postgresql"
fi

PGDATA="$PGVAR/data"
PGLOG="$PGDATA/serverlog"

INITDB="initdb"
if [ "$(which $INITDB | wc -l)" != '1' ]; then
  INITDB="/usr/lib/postgresql/${postgres_version}/bin/initdb"
fi

POSTGRES="postgres"
if [ "$(which $POSTGRES | wc -l)" != '1' ]; then
  POSTGRES="/usr/lib/postgresql/${postgres_version}/bin/postgres"
fi

if [ ! -d "$PGDATA" ]; then
  mkdir $PGDATA
  chown -R $PGUSER:$PGUSER $PGDATA
  # Init postgres
  INIT_COMMAND="$INITDB --locale en_US.UTF-8 -E UTF8 -D '$PGDATA'"
  su $PGUSER -c "$INIT_COMMAND"
fi

echo "[+] Starting PostgreSQL ..." 1>&2
START_COMMAND="$POSTGRES -D '$PGDATA' &"
su $PGUSER -c "$START_COMMAND"  >> $PGLOG 2>$PGLOG

# Wait until the postgres server starts.
while [ "$(cat $PGLOG | grep 'ready' | wc -l)" = "0" ]; do
  if [ "$(cat $PGLOG | grep 'fail' | wc -l)" != "0" ]; then
    echo "[!] Failed to start the postgres server"
    exit 1
  fi ;
done

echo "[+] PostgreSQL server successfully started!"
