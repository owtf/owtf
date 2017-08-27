db_clean:
		@echo "--> Dropping the database"
		-echo '\n' | sh owtf/scripts/db_setup.sh clean

db_init:
		@echo "--> Initializing the database"
		-echo '\n' | sh owtf/scripts/db_setup.sh init

install_dependencies:
		@echo "--> Installing Kali dependencies"
		sudo apt-get install -y python git
		sudo apt-get install -y vfb xserver-xephyr libxml2-dev libxslt-dev libssl-dev zlib1g-dev gcc python-all-dev \
			python-pip postgresql-server-dev-all postgresql-client postgresql-client-common postgresql  \
			libcurl4-openssl-dev proxychains tor

opt_tools:
		sudo apt-get install -y lbd gnutls-bin arachni o-saft metagoofil

