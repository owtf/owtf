#!/usr/bin/perl
########################################################################
# Copyright 2010 Sunera, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################################################
# Contact:		Chris Sullo (csullo [at] sunera [.] com)
# Blog:			http://security.sunera.com/
#
# Program Name:		CMS Explorer
# Purpose:		Discover plugins/themes installed in CMS software
# Version:		1.0
# Code Repo:            http://code.google.com/p/cms-explorer/
# Dependencies:         LibWhisker
#                       Getopt::Long
# 			OSVDB API key (optional): http://osvdb.org/api/about
########################################################################

use strict;
use LW2;
use Getopt::Long;

# Set defaults
use vars qw/%OPTIONS %request %request_bootstrap @plugins @themes %URLS %EXPQ/;
$URLS{'wp_svn_plugin'}       = "http://svn.wp-plugins.org/";
$URLS{'wp_svn_theme'}        = "http://themes.svn.wordpress.org/";
$URLS{'drupal_cvs_modules'}  = "http://drupalcode.org/viewvc/drupal/contributions/modules/";
$URLS{'drupal_cvs_modules2'} = "http://drupalcode.org/viewvc/drupal/drupal/modules/";
$URLS{'drupal_cvs_themes'}   = "http://drupalcode.org/viewvc/drupal/contributions/themes/";
$URLS{'drupal_cvs_themes2'}  = "http://drupalcode.org/viewvc/drupal/drupal/themes/";
LW2::http_init_request(\%request);

# Load OSVDB API key
my $osvdb_api_key = osvdb_load_apikey();
if ($osvdb_api_key eq '') {
    print "*****************************************************************\n";
    print "WARNING: No osvdb.org API key defined, searches will be disabled.\n";
    print "*****************************************************************\n";
    }

# Check options & setup
parse_options();

#############################################################
print "\n*******************************************************\n";
print "Beginning run against $OPTIONS{'url'}...\n";

my (@theme_finds, @plugin_finds) = ();

# Load & brute force themes
if ($OPTIONS{'checkthemes'}) {
    print "Testing themes from $OPTIONS{'themefile'}...\n";
    my @themes = get_file($OPTIONS{'themefile'});
    my @it;
    brute($OPTIONS{'uri'}, \@themes, \@it, "theme");
    foreach my $find (@it) {
        print "Theme Installed:\t\t$find\n";
        push(@theme_finds, $find);
        }
    }

# Load & brute force plugins
if ($OPTIONS{'checkplugins'}) {
    print "Testing plugins...\n";
    my @plugins = get_file($OPTIONS{'pluginfile'});
    my @ip;
    brute($OPTIONS{'uri'}, \@plugins, \@ip, "plugin");
    foreach my $find (@ip) {
        print "Plugin Installed:\t\t$find\n";
        push(@plugin_finds, $find);
        }
    }

# Explore
if ($OPTIONS{'explore'}) {
    print "\n*******************************************************\n";
    print "Running explorer...\n";

    print "Looking for theme files...\n" unless !$OPTIONS{'checkthemes'};
    foreach my $find (@theme_finds) {
        my $f = $find;
        $f =~ s/^themes\///;
        if ($OPTIONS{'type'} eq 'wp') {
            get_svn_files($URLS{'wp_svn_theme'} . $f, $OPTIONS{'uri'} . "themes/");
            }
        elsif ($OPTIONS{'type'} eq 'drupal') {
            get_cvs_files($URLS{'drupal_cvs_themes'} . $f, $OPTIONS{'uri'} . "themes/");
            }
        }

    print "Looking for plugin/module files...\n" unless !$OPTIONS{'checkplugins'};
    foreach my $find (@plugin_finds) {
        my $f = $find;
        $f =~ s/^(?:plugins|modules)\///;
        if ($OPTIONS{'type'} eq 'wp') {
            get_svn_files($URLS{'wp_svn_plugin'} . $f . "/trunk/", $OPTIONS{'uri'} . "plugins");
            }
        elsif ($OPTIONS{'type'} eq 'drupal') {
            get_cvs_files($URLS{'drupal_cvs_modules'} . $f, $OPTIONS{'uri'} . "modules");
            }
        }

    # try files (through bootstrap proxy)
    print "\n*******************************************************\n";
    if ($OPTIONS{'bsproxy_host'} ne '') {
        print "Requesting files through bootstrap proxy...\n";
        }
    else {
        print "Requesting files...\n";
        }

    my %result;
    my $ctr = 0;
    foreach my $file (keys %EXPQ) {
        $ctr++;
        if ($OPTIONS{'bsproxy_host'} ne '') {
            $request_bootstrap{'whisker'}->{'uri'} = $file;
            LW2::http_fixup_request(\%request_bootstrap);
            LW2::http_do_request(\%request_bootstrap, \%result);
            }
        else {
            $request{'whisker'}->{'uri'} = $file;
            LW2::http_fixup_request(\%request);
            LW2::http_do_request(\%request, \%result);
            }
        if (($OPTIONS{'verbosity'} eq '3') || ($OPTIONS{'bsproxy_host'} eq '')) {
            print "Explore:\t$result{'whisker'}->{'code'}\t$file\n";
            }
        elsif (   ($OPTIONS{'verbosity'} eq '2')
               && ($OPTIONS{'bsproxy_host'} ne '')
               && (($ctr % 10) eq 0)) {
            print "Explore:\t$result{'whisker'}->{'code'}\t$file\n";
            }
        elsif (   ($OPTIONS{'verbosity'} eq '1')
               && ($OPTIONS{'bsproxy_host'} ne '')
               && (($ctr % 100) eq 0)) {
            print "Explore:\t$result{'whisker'}->{'code'}\t$file\n";
            }
        }
    }

# Print summary & OSVDB search
print "\n*******************************************************\n";
print "Summary:\n";
foreach my $find (@theme_finds) {
    print "Theme Installed:\t\t$find\n";
    print "\tURL\t\t\t" . $OPTIONS{'url'} . $find . "\n";
    if ($OPTIONS{'type'} eq 'joomla') {
        print osvdb_search($find, $OPTIONS{'type'});
        }
    elsif ($OPTIONS{'type'} eq 'wp') {
        print "\tSVN\t\t\thttp://themes.svn.wordpress.org/" . $find . "\n";
        print osvdb_search($find, $OPTIONS{'type'});
        }
    elsif ($OPTIONS{'type'} eq 'drupal') {
        print "\tCVS\t\t\thttp://drupalcode.org/viewvc/drupal/contributions/" . $find . "\n";
        print osvdb_search($find, $OPTIONS{'type'});
        }
    }

foreach my $find (@plugin_finds) {
    print "Plugin Installed:\t\t$find\n";
    print "\tURL\t\t\t" . $OPTIONS{'url'} . $find . "\n";
    if (($OPTIONS{'type'} eq 'joomla') && ($find =~ /^components/)) {
        my $com = $find;
        $com =~ s/^components\///;
        $com =~ s/\/$//;
        print "\tURL\t\t\t" . $OPTIONS{'url'} . "index.php?option=" . $com . "\n";
        print osvdb_search($com, $OPTIONS{'type'});
        }
    elsif ($OPTIONS{'type'} eq 'wp') {
        print "\tSVN\t\t\thttp://svn.wp-plugins.org/" . $find . "trunk/\n"
          unless $find eq 'hello.php';
        print osvdb_search($find, $OPTIONS{'type'});
        }
    elsif ($OPTIONS{'type'} eq 'drupal') {
        print "\tCVS\t\t\thttp://drupalcode.org/viewvc/drupal/contributions/" . $find
          . "\n";
        print osvdb_search($find, $OPTIONS{'type'});
        }
    }

exit;

#############################################################
sub osvdb_load_apikey {
    if ((-e "osvdb.key") && (-r "osvdb.key")) {
        open(IN, "<osvdb.key") || die print "ERROR: Unable to open osvdb.key: $!\n";
        my @F = <IN>;
        close(IN);
        chomp($F[0]);
        return $F[0];
        }
    return;
    }

#############################################################
sub osvdb_search {
    if (!$OPTIONS{'osvdb'}) { return; }
    if ($osvdb_api_key eq '') { return; }
    my $string = $_[0] || return;
    my $product = $_[1];
    if ($product eq 'wp') { $product = "wordpress"; }
    $string =~
      s/^(?:wp-content\/)?(?:modules|themes|templates|components|(?:wp-content\/|plugins|themes))\///;
    $string =~ s/\/$//;
    my $url = "http://osvdb.org/search?format=csv&key=" . $osvdb_api_key;
    $url .= "&search%5Btext_type%5D=alltext&search%5Bvuln_title%5D=" . $string . "%20" . $product;
    my ($code, $data) = LW2::get_page($url);
    my %entries;

    if ($OPTIONS{'verbosity'} > '1') {
        print "OSVDB search for \"$string $product\" result code $code size "
          . length($data) . "\n";
        }
    if (($code eq 200) && (length($data) > 1)) {
        foreach my $line (split(/(?:\n|\r)/, $data)) {
            if ($line !~ /^\d+,/) { next; }    # not an entry
            my @data = parse_csv($line);
            $entries{ $data[0] } = $data[1];
            }
        my $output;
        foreach my $id (sort keys %entries) {
            $output .= "\thttp://osvdb.org/" . $id . "\t" . $entries{$id} . "\n";
            }
        return $output;
        }
    return;
    }

#############################################################
sub parse_csv {
    my $text = $_[0] || return;
    my @new = ();
    push(@new, $+) while $text =~ m{
      "([^\"\\]*(?:\\.[^\"\\]*)*)",?
       |  ([^,]+),?
      | ,
   }gx;
    push(@new, undef) if substr($text, -1, 1) eq ',';
    return @new;
    }

#############################################################
sub brute {
    my ($base, $tests, $out, $type) = @_;
    my (@finds, %result);
    my $ctr   = 1;
    my $total = @$tests;
    map {
        my $f = $_;
        $request{'whisker'}->{'uri'} = $base . $f;
        LW2::http_fixup_request(\%request);
        LW2::http_do_request(\%request, \%result);
        if ($OPTIONS{'verbosity'} eq '3') {
            print "$ctr/$total:\t$result{'whisker'}->{'code'}\t$base$f\n";
            }
        elsif (($OPTIONS{'verbosity'} eq '2') && (($ctr % 10) eq 0)) {
            print "$ctr/$total:\t$result{'whisker'}->{'code'}\t$base$f\n";
            }
        elsif (($OPTIONS{'verbosity'} eq '1') && (($ctr % 100) eq 0)) {
            print "$ctr/$total:\t$result{'whisker'}->{'code'}\t$base$f\n";
            }
        $ctr++;
        if ($result{'whisker'}->{'code'} =~ /(?:403|[52]\d\d|2\d\d)/) {
            push(@{$out}, $f);
            if ($OPTIONS{'verbosity'} =~ /[1-3]/) {
                print "Installed:\t$f\n";
                }

            # and route through bootstrap proxy, if desired
            if ($OPTIONS{'bsproxy_host'} ne '') {
                $request_bootstrap{'whisker'}->{'uri'} = $base . $f;
                LW2::http_fixup_request(\%request_bootstrap);
                LW2::http_do_request(\%request_bootstrap, \%result);
                }
            }
        } @$tests;
    }

#############################################################
sub update {
    my %files;
    $files{'wp_plugins.txt'}     = "http://svn.wp-plugins.org/";
    $files{'wp_themes.txt'}      = "http://themes.svn.wordpress.org/";
    $files{'drupal_themes.txt'}  = "http://drupalcode.org/viewvc/drupal/contributions/themes/";
    $files{'drupal_plugins.txt'} = "http://drupalcode.org/viewvc/drupal/contributions/modules/";

    foreach my $file (keys %files) {
        my ($code, $data) = LW2::get_page($files{$file});
        if ($code ne '200') { print "$code error getting $files{$file}\n"; }
        my @items = ();
        my $pre   = "";
        if ($file eq 'drupal_plugins.txt') {
            $pre = "modules";

            # From the drupal/drupal tree...
            @items = ('modules/actions/',    'modules/aggregator/',
                      'modules/archive/',    'modules/block/',
                      'modules/blog/',       'modules/blogapi/',
                      'modules/book/',       'modules/color/',
                      'modules/comment/',    'modules/contact/',
                      'modules/contextual/', 'modules/dashboard/',
                      'modules/dblog/',      'modules/drupal/',
                      'modules/field/',      'modules/field_ui/',
                      'modules/file/',       'modules/filter/',
                      'modules/forum/',      'modules/help/',
                      'modules/image/',      'modules/legacy/',
                      'modules/locale/',     'modules/menu/',
                      'modules/node/',       'modules/openid/',
                      'modules/overlay/',    'modules/page/',
                      'modules/path/',       'modules/php/',
                      'modules/ping/',       'modules/poll/',
                      'modules/profile/',    'modules/rdf/',
                      'modules/search/',     'modules/shortcut/',
                      'modules/simpletest/', 'modules/statistics/',
                      'modules/story/',      'modules/syslog/',
                      'modules/system/',     'modules/taxonomy/',
                      'modules/throttle/',   'modules/toolbar/',
                      'modules/tracker/',    'modules/translation/',
                      'modules/trigger/',    'modules/update/',
                      'modules/upload/',     'modules/user/',
                      'modules/watchdog/'
                      );
            }
        elsif ($file eq 'drupal_themes.txt') {
            $pre = "themes";

            # From the drupal/drupal tree...
            @items = ('themes/bluemarine', 'themes/chameleon',
                      'themes/garland',    'themes/goofy',
                      'themes/jeroen',     'themes/marvin',
                      'themes/pushbutton', 'themes/seven',
                      'themes/slate',      'themes/stark',
                      'themes/trillian',   'themes/unconed',
                      'themes/yaroon'
                      );
            }
        elsif ($file eq 'wp_plugins.txt') {
            $pre   = "wp-content/plugins/";
            @items = ('wp-content/plugins/hello.php');
            }
        elsif ($file eq 'wp_themes.txt') {
            $pre = "wp-content/themes/";
            @items = ('wp-content/themes/classic/', 'themes/default');
            }

        foreach my $line (split(/\n/, $data)) {
            if ($line !~ /(<li><a|View directory)/) { next; }
            my @d = split(/\"/, $line);
            if (($file =~ /^wp_/) && ($d[1] ne '')) { push(@items, $pre . $d[1]); }
            if (($file =~ /^drupal_/) && ($d[3] ne '')) {
                $d[3] =~ s/viewvc\/drupal\/(contributions|drupal)\/(modules|themes)\///;
                push(@items, $pre . $d[3]);
                }
            }
        if ($#items > 1) {
            open(OUT, ">$file") || die print STDERR "** ERROR: failed to open '$file': $! **\n";
            print OUT join("\n", @items);
            close(OUT);
            print "$file updated with " . $#items . " entries\n";
            }
        }
    exit;
    }

#############################################################
sub parse_options {
    GetOptions("url=s"        => \$OPTIONS{'url'},
               "pluginfile=s" => \$OPTIONS{'pluginfile'},
               "themefile=s"  => \$OPTIONS{'themefile'},
               "type=s"       => \$OPTIONS{'type'},
               "themes"       => \$OPTIONS{'checkthemes'},
               "explore"      => \$OPTIONS{'explore'},
               "help"         => \$OPTIONS{'help'},
               "osvdb"        => \$OPTIONS{'osvdb'},
               "plugins"      => \$OPTIONS{'checkplugins'},
               "proxy=s"      => \$OPTIONS{'proxy_host'},
               "bsproxy=s"    => \$OPTIONS{'bsproxy_host'},
               "update"       => \$OPTIONS{'update'},
               "verbosity=i"  => \$OPTIONS{'verbosity'}
               ) || die usage("^^^^^^^^^^^^^^  ERROR ^^^^^^^^^^^^^^\n");

    if ($OPTIONS{'help'}) { usage(); }

    if ($OPTIONS{'update'}) { update(); }

    if ($OPTIONS{'url'} eq '') { usage("\nERROR: Missing -url\n"); }
    if ($OPTIONS{'url'} !~ /\/$/) { $OPTIONS{'url'} .= "/"; }

    if ($OPTIONS{'proxy_host'} ne '') {
        if ($OPTIONS{'proxy_host'} !~ /^https?\:\/\//) {
            $OPTIONS{'proxy_host'} = "http://$OPTIONS{'proxy_host'}";
            }
        my @hostdata = LW2::uri_split($OPTIONS{'proxy_host'});
        $OPTIONS{'proxy_host'} = $hostdata[2];
        $OPTIONS{'proxy_port'} = $hostdata[3] || 80;
        }

    if ($OPTIONS{'bsproxy_host'} ne '') {
        if ($OPTIONS{'bsproxy_host'} !~ /^https?\:\/\//) {
            $OPTIONS{'bsproxy_host'} = "http://$OPTIONS{'bsproxy_host'}";
            }
        my @hostdata = LW2::uri_split($OPTIONS{'bsproxy_host'});
        $OPTIONS{'bsproxy_host'} = $hostdata[2];
        $OPTIONS{'bsproxy_port'} = $hostdata[3] || 80;
        }

    $OPTIONS{'type'} = lc($OPTIONS{'type'});

    if (($OPTIONS{'type'} eq 'wp') || ($OPTIONS{'type'} eq 'wordpress')) {
        $OPTIONS{'runprefix'} = "wp_";
        $OPTIONS{'type'}      = "wp";
        }
    elsif ($OPTIONS{'type'} eq 'drupal') {
        $OPTIONS{'runprefix'} = "drupal_";
        }
    elsif (($OPTIONS{'type'} eq 'joomla') || ($OPTIONS{'type'} eq 'mambo')) {
        $OPTIONS{'runprefix'} = "joomla_";
        }
    else {
        usage("\nERROR: Must specify -type\n");
        }

    if (!$OPTIONS{'checkthemes'} && !$OPTIONS{'checkplugins'}) {
        $OPTIONS{'checkplugins'} = 1;
        $OPTIONS{'checkthemes'}  = 1;
        }
    if (!defined($OPTIONS{'themefile'}) || $OPTIONS{'themefile'} eq '') {
        $OPTIONS{'themefile'} = $OPTIONS{'runprefix'} . "themes.txt";
        }
    if (!defined($OPTIONS{'pluginfile'}) || $OPTIONS{'pluginfile'} eq '') {
        $OPTIONS{'pluginfile'} = $OPTIONS{'runprefix'} . "plugins.txt";
        }
    if ($OPTIONS{'verbosity'} =~ /[^1-3]/ || $OPTIONS{'verbosity'} eq '') {
        $OPTIONS{'verbosity'} = 0;
        }

    # split host / path
    ($OPTIONS{'uri'}, $OPTIONS{'protocol'}, $OPTIONS{'host'}) = LW2::uri_split($OPTIONS{'url'});
    if ($OPTIONS{'uri'} !~ /\/$/) { $OPTIONS{'uri'} .= "/"; }

    # populate %request
    LW2::uri_split($OPTIONS{'url'}, \%request);
    $request{'User-Agent'}           = 'Mozilla/5.0 (en-US; rv:1.9.1.7) Firefox/3.5.7';
    $request{'whisker'}->{'version'} = '1.1';
    $request{'whisker'}->{'method'}  = 'HEAD';
    if ($OPTIONS{'proxy_host'} ne '') {
        $request{'whisker'}->{'proxy_host'} = $OPTIONS{'proxy_host'};
        $request{'whisker'}->{'proxy_port'} = $OPTIONS{'proxy_port'};
        }

    if ($OPTIONS{'bsproxy_host'} ne '') {
        LW2::utils_request_clone(\%request, \%request_bootstrap);
        $request_bootstrap{'whisker'}->{'proxy_host'} = $OPTIONS{'bsproxy_host'};
        $request_bootstrap{'whisker'}->{'proxy_port'} = $OPTIONS{'bsproxy_port'};
        }
    }

#############################################################
sub get_cvs_files {
    my $baseurl = $_[0] || return;
    my $url = $_[1];
    my ($code, $data) = LW2::get_page($baseurl);
    if ($code eq '404') {
        my $dir = $baseurl;
        $dir =~ s/$URLS{'drupal_cvs_modules'}//;
        ($code, $data) = LW2::get_page($URLS{'drupal_cvs_modules2'} . $dir);
        }
    foreach my $line (split(/\n/, $data)) {
        if ($line !~ /View (directory|file)/) { next; }
        my @d = split(/\"/, $line);
        next if $d[3] eq './';
        next if $d[3] eq '../';
        my $dir = $baseurl;
        if ($d[3] =~ /\/$/) {
            my @h = LW2::uri_split($baseurl);
            get_cvs_files($h[1] . "://" . $h[2] . "/" . $d[3], $url);
            }
        else {
            $d[3] =~ s/\?.*$//;
            $d[3] =~ s/viewvc\/drupal\/(contributions|drupal)\/(modules|themes)\///;
            my $temp = $url . $d[3];
            $temp =~ s/\/\//\//g;
            $EXPQ{$temp} = 0;
            }
        }
    }

#############################################################
sub get_svn_files {
    my $baseurl = $_[0] || return;
    my $wpurl = $_[1];
    my ($code, $data) = LW2::get_page($baseurl);
    foreach my $line (split(/\n/, $data)) {
        if ($line !~ /<li><a/) { next; }
        my @d = split(/\"/, $line);
        next if $d[1] eq './';
        next if $d[1] eq '../';
        my $dir = $baseurl;
        if ($dir =~ /$URLS{'wp_svn_theme'}/) {
            $dir =~ s/$URLS{'wp_svn_theme'}//;
            my @parts = split(/\//, $dir);
            undef($parts[1]);
            $dir = join("/", @parts);
            $dir =~ s/\/\//\//g;
            }
        if ($dir =~ /$URLS{'wp_svn_plugin'}/) {
            $dir =~ s/$URLS{'wp_svn_plugin'}//;
            $dir =~ s/\/trunk\///;
            }

        if ($d[1] =~ /\/$/) {
            get_svn_files($baseurl . $d[1], $wpurl);
            }
        else {
            if ($d[1] !~ /^\//) { $d[1] = "/$d[1]"; }
            if ($dir !~ /^\//) { $dir = "/$dir"; }
            $EXPQ{ $wpurl . $dir . $d[1] } = 0;
            }
        }
    }

#############################################################
sub get_file {
    my $file = $_[0] || return;
    my @items;
    open(IN, "<$file") || die print STDERR "** ERROR: failed to open '$file': $! **\n";
    while (<IN>) {
        chomp;
        s/^\///;
        push(@items, $_);
        }
    close(IN);
    return @items;
    }

#############################################################
sub usage {
    print "$_[0]\n";
    print "$0 -url url -type type [options]\n";
    print "\nOptions:\n";
    print "\t-bsproxy+ 	Proxy to route findings through (fmt: host:port)\n";
    print "\t-explore	Look for files in the theme/plugin dir\n";
    print "\t-help           This screen\n";
    print "\t-osvdb		Do OSVDB check for finds\n";
    print "\t-plugins	Look for plugins (default: on)\n";
    print "\t-pluginfile+	Plugin file list\n";
    print "\t-proxy+ 	Proxy for requests (fmt: host:port)\n";
    print "\t-themes		Look for themes (default: on)\n";
    print "\t-themefile+	Theme file list (default: themes.txt)\n";
    print "\t-type+*		CMS type: Drupal, Wordpress, Joomla, Mambo\n";
    print "\t-update 	Update lists from Wordpress/Drupal (over-writes text files)\n";
    print "\t-url+*		Full url to app's base directory\n";
    print "\t-verbosity+ 	1-3\n";
    print "\n";
    print "\t+ Requires value\n";
    print "\t* Required option\n";
    exit;
    }

