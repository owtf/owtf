# NOPOD NOTICE: the documentation and whitespace have been stripped
# from this file in order to reduce filesize.
#

#!/usr/bin/perl
# LW2 version 2.5
#   LW2 Copyright (c) 2009, Jeff Forristal (wiretrip.net)
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without 
#   modification, are permitted provided that the following conditions 
#   are met:
#
#   - Redistributions of source code must retain the above copyright 
#   notice, this list of conditions and the following disclaimer.
#
#   - Redistributions in binary form must reproduce the above copyright 
#   notice, this list of conditions and the following disclaimer in the 
#   documentation and/or other materials provided with the distribution.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
#   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
#   COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
#   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
#   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
#   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
#   ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
#   POSSIBILITY OF SUCH DAMAGE.
package LW2;
$LW2::VERSION="2.5";
$PACKAGE='LW2';
BEGIN {
package LW2;
$PACKAGE='LW2';
$LW_SSL_LIB          = 0;
$LW_SSL_KEEPALIVE    = 0;
$LW_NONBLOCK_CONNECT = 1;
$_SSL_LIBRARY = undef;
eval "use Socket";
if ( !$@ ) {
eval "use Net::SSLeay";    # do we have SSL support?
if ( !$@ ) {
$LW_SSL_LIB   = 1;
$_SSL_LIBRARY = 'Net::SSLeay';
Net::SSLeay::load_error_strings();
Net::SSLeay::SSLeay_add_ssl_algorithms();
Net::SSLeay::randomize();
}
else {
eval "use Net::SSL";
if ( !$@ ) {
$LW_SSL_LIB   = 2;
$_SSL_LIBRARY = 'Net::SSL';
}
}
if ( $^O !~ /Win32/ ) {
eval "use POSIX qw(:errno_h :fcntl_h)";
if ($@) { $LW_NONBLOCK_CONNECT = 0; }
}
else {
*EINPROGRESS = sub { 10036 };
*EWOULDBLOCK = sub { 10035 };
}
}
} # BEGIN
sub auth_brute_force {
my ( $auth_method, $hrin, $user, $pwordref, $dom, $fail_code ) = @_;
my ( $P, %hout );
$fail_code ||= 401;
return undef if ( !defined $auth_method || length($auth_method) == 0 );
return undef if ( !defined $user        || length($user) == 0 );
return undef if ( !( defined $hrin     && ref($hrin) ) );
return undef if ( !( defined $pwordref && ref($pwordref) ) );
map {
( $P = $_ ) =~ tr/\r\n//d;
auth_set( $auth_method, $hrin, $user, $P, $dom );
return undef if ( http_do_request( $hrin, \%hout ) );
return $P if ( $hout{whisker}->{code} != $fail_code );
} @$pwordref;
return undef;
}
sub auth_unset {
my $href = shift;
return if ( !defined $href || !ref($href) );
delete $$href{Authorization};
delete $$href{'Proxy-Authorization'};
delete $$href{whisker}->{auth_callback};
delete $$href{whisker}->{auth_proxy_callback};
delete $$href{whisker}->{auth_data};
delete $$href{whisker}->{auth_proxy_data};
}
sub auth_set {
my ( $method, $href, $user, $pass, $domain ) = ( lc(shift), @_ );
return if ( !( defined $href && ref($href) ) );
return if ( !defined $user || !defined $pass );
if ( $method eq 'basic' ) {
$$href{'Authorization'} =
'Basic ' . encode_base64( $user . ':' . $pass, '' );
}
if ( $method eq 'proxy-basic' ) {
$$href{'Proxy-Authorization'} =
'Basic ' . encode_base64( $user . ':' . $pass, '' );
}
if ( $method eq 'ntlm' ) {
http_close($href);
$$href{whisker}->{auth_data} = ntlm_new( $user, $pass, $domain );
$$href{whisker}->{auth_callback} = \&_ntlm_auth_callback;
}
if ( $method eq 'proxy-ntlm' ) {
utils_croak('',"auth_set: proxy-ntlm auth w/ SSL not currently supported")
if ( $href->{whisker}->{ssl} > 0 );
http_close($href);
$$href{whisker}->{auth_proxy_data} = ntlm_new( $user, $pass, $domain );
$$href{whisker}->{auth_proxy_callback} = \&_ntlm_auth_proxy_callback;
}
}
sub cookie_new_jar {
return {};
}
sub cookie_read {
my ( $count, $jarref, $hrs, $hrq, $rej ) = ( 0, @_ );
return 0 if ( !( defined $jarref && ref($jarref) ) );
return 0 if ( !( defined $hrs   && ref($hrs) ) );
return 0
if (
!(
defined $$hrs{whisker}->{cookies}
&& ref( $$hrs{whisker}->{cookies} )
)
);
my @opt;
if(defined $hrq && ref($hrq)){
push @opt, $hrq->{whisker}->{host};
my $u = $hrq->{whisker}->{uri};
$u=~s#/.*?$##;
$u='/' if($u eq '');
push @opt, $u, $rej;
}
foreach ( @{ $hrs->{whisker}->{cookies} } ) {
cookie_parse( $jarref, $_ , @opt);
$count++;
}
return $count;
}
sub cookie_parse {
my ( $jarref, $header ) = (shift, shift);
my ( $Dd, $Dp, $R ) = (shift, shift, shift||0);
return if ( !( defined $jarref && ref($jarref) ) );
return if ( !( defined $header && length($header) > 0 ) );
my @C = ( undef, undef, undef, undef, 0 );
$header =~ tr/\r\n//d;
my ($f,%seen,$n,$t) = (1);
while( length($header) ){
$header =~ s/^[ \t]+//;
last if(!($header =~ s/^([^ \t=;]+)//));
my $an = $1;
my $av = undef;
$header =~ s/^[ \t]+//;
if(substr($header,0,1) eq '='){
$header=~s/^=[ \t]*//;
if(substr($header,0,1) eq '"'){
my $p = index($header,'"',1);
last if($p == -1);
$av = substr($header,1,$p-1);
substr($header,0,$p+1)='';
} else {
$av = $1 if($header =~ s/^([^ \t;,]*)//);
}
} else {
my $p = index($header,';');
substr($header,0,$p)='';
}
$header =~ s/^.*?;//;
if($f){
return if(!defined $av);
($f,$n,$C[0])=(0,$an,$av);
} else {
$seen{$an}=$av if(!exists $seen{$an});
}
}
return if(!defined $n || $n eq '');
my $del = 0;
$del++ if($C[0] eq '');
$del++ if(defined $seen{'max-age'} && $seen{'max-age'} eq '0');
if($del){
delete $$jarref{$n} if exists $$jarref{$n};			
return;
}
if(defined $seen{domain} && $seen{domain} ne ''){
$t = $seen{domain};
$t='.'.$t if(substr($t,0,1) ne '.' && !_is_ip_address($t));
} else {
$t=$Dd;
}
$t=~s/\.+$// if(defined $t);
$C[1]=$t;
if(defined $seen{path}){
$t = $seen{path};
} else {
$t=$Dp || '/';
}
$t=~s#/+$##;
$t='/' if(substr($t,0,1) ne '/');
$C[2]=$t;
$C[4]=1 if(exists $seen{secure});
return if($R && !_is_valid_cookie_match($C[1], $C[2], $Dd, $Dp));
$$jarref{$n} = \@C;
}
sub _is_ip_address {
my $n = shift;
return 1 if($n=~/^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$/);
return 0;
}
sub _is_valid_cookie_match {
my ($cd, $cp, $td, $tp) = @_;
return 0 if(index($tp,$cp)!=0);
if(substr($cd,0,1) eq '.'){
if( $td =~ /(.+)$cd$/ ){
return 1 if(index($1,'.') == -1);
}
return 0;
} else {
return 0 if($cd ne $td);
}
return 1;
}
sub cookie_write {
my ( $jarref, $hin, $override ) = @_;
my ( $name, $out ) = ( '', '' );
return if ( !( defined $jarref && ref($jarref) ) );
return if ( !( defined $hin    && ref($hin) ) );
$override = $override || 0;
$$hin{'whisker'}->{'ssl'} = $$hin{'whisker'}->{'ssl'} || 0;
foreach $name ( keys %$jarref ) {
next if ( $name eq '' );
if($override){
$out .= "$name=$$jarref{$name}->[0];";
next;
}
next if ( $$hin{'whisker'}->{'ssl'} == 0 && $$jarref{$name}->[4] > 0 );
if ( $$hin{'whisker'}->{'host'} =~ /$$jarref{$name}->[1]$/i
&& $$hin{'whisker'}->{'uri'} =~ /^$$jarref{$name}->[2])/ )
{
$out .= "$name=$$jarref{$name}->[0];";
}
}
if ( $out ne '' ) { $$hin{'Cookie'} = $out; }
}
sub cookie_get {
my ( $jarref, $name ) = @_;
return undef if ( !( defined $jarref && ref($jarref) ) );
if ( defined $$jarref{$name} ) {
return @{ $$jarref{$name} };
}
return undef;
}
sub cookie_get_names {
my ( $jarref, $name ) = @_;
return undef if ( !( defined $jarref && ref($jarref) ) );
return keys %$jarref;
}
sub cookie_get_valid_names {
my ( $jarref, $domain, $url, $ssl ) = @_;
return () if ( !( defined $jarref && ref($jarref) ) );
return () if ( !defined $domain || $domain eq '' );
return () if ( !defined $url || $url eq '' );
$ssl ||= 0;
my (@r, $name);
foreach $name ( keys %$jarref ) {
next if ( $name eq '' );
next if ( $$jarref{$name}->[4] > 0 && $ssl == 0 );
if ( $domain =~ /$$jarref{$name}->[1]$/i
&& $url =~ /^$$jarref{$name}->[2])/i ) {
push @r, $name;
}
}
return @r;
}
sub cookie_set {
my ( $jarref, $name, $value, $domain, $path, $expire, $secure ) = @_;
my @construct;
return if ( !( defined $jarref && ref($jarref) ) );
return if ( $name eq '' );
if ( !defined $value || $value eq '' ) {
delete $$jarref{$name};
return;
}
$path   = $path   || '/';
$secure = $secure || 0;
@construct = ( $value, $domain, $path, undef, $secure );
$$jarref{$name} = \@construct;
}
%_crawl_config = (
'save_cookies'         => 0,
'reuse_cookies'        => 1,
'save_offsites'        => 0,
'save_non_http'        => 0,
'follow_moves'         => 1,
'url_limit'            => 1000,
'use_params'           => 0,
'params_double_record' => 0,
'skip_ext'             => {
gif => 1,
jpg => 1,
png => 1,
gz  => 1,
swf => 1,
pdf => 1,
zip => 1,
wav => 1,
mp3 => 1,
asf => 1,
tgz => 1
},
'save_skipped'    => 0,
'save_referrers'  => 0,
'use_referrers'   => 1,
'do_head'         => 0,
'callback'        => 0,
'netloc_bug'      => 1,
'normalize_uri'   => 1,
'source_callback' => 0
);
%_crawl_linktags = (
'a'          => 'href',
'applet'     => [qw(codebase archive code)],
'area'       => 'href',
'base'       => 'href',
'bgsound'    => 'src',
'blockquote' => 'cite',
'body'       => 'background',
'del'        => 'cite',
'embed'      => [qw(src pluginspage)],
'form'       => 'action',
'frame'      => [qw(src longdesc)],
'iframe'     => [qw(src longdesc)],
'ilayer'     => 'background',
'img'        => [qw(src lowsrc longdesc usemap)],
'input'      => [qw(src usemap)],
'ins'        => 'cite',
'isindex'    => 'action',
'head'       => 'profile',
'layer'      => [qw(background src)],
'link'       => 'href',
'object' => [qw(codebase data archive usemap)],
'q'      => 'cite',
'script' => 'src',
'table'  => 'background',
'td'     => 'background',
'th'     => 'background',
'xmp'    => 'href',
);
sub crawl_new {
my ( $start, $depth, $reqref, $trackref ) = @_;
my %X;
return undef if ( !defined $start  || !defined $depth );
return undef if ( !defined $reqref || !ref($reqref) );
$trackref = {} if ( !defined $trackref || !ref($trackref) );
$X{track}   = $trackref;
$X{request} = $reqref;
$X{depth}   = $depth || 2;
$X{start}   = $start;
$X{magic}   = 7340;
$X{reset} = sub {
$X{errors}      = [];    # all errors encountered
$X{urls}        = [];    # temp; used to hold all URLs on page
$X{server_tags} = {};    # all server tags found
$X{referrers}   = {};    # who refers to what URLs
$X{offsites}    = {};    # all URLs that point offsite
$X{response}    = {};    # temp; the response hash
$X{non_http}    = {};    # all non_http URLs found
$X{cookies}     = {};    # all cookies found
$X{forms}       = {};    # all forms found
$X{jar}         = {};    # temp; cookie jar
$X{url_queue}   = [];    # temp; URLs to still fetch
$X{config} = {};
%{ $X{config} } = %_crawl_config;
%{ $X{track} } = ();
$X{parsed_page_count} = 0;
};
$X{crawl} = sub { crawl( \%X, @_ ) };
$X{reset}->();
return \%X;
}
{    # START OF CRAWL CONTAINER
sub crawl {
my ( $C, $START, $MAX_DEPTH ) = @_;
return undef if ( !defined $C || !ref($C) || $C->{magic} != 7340 );
my $CONFIG = $C->{config};
my $TRACK  = $C->{track};
my $URLS   = $C->{urls};
my $RESP   = $C->{response};
my $REQ    = $C->{request};
my $Q      = $C->{url_queue};
$START ||= $C->{start};
$C->{depth} = $MAX_DEPTH || $C->{depth};
my ( $COUNT, $T, @ST ) = ( 0, '' );
my @v = uri_split($START);
my $error = undef;
$error = 'Start protocol not http or https'
if ( $v[1] ne 'http' && $v[1] ne 'https' );
$error = 'Bad start host' if ( !defined $v[2] || $v[2] eq '' );
push( @{ $C->{errors} }, $error ) && return undef if ( defined $error );
@ST = ( $v[2], $v[3], $v[0], 1, '', '' );
$REQ->{whisker}->{ssl}  = 1 if ( $v[1] eq 'https' );
$REQ->{whisker}->{host} = $ST[0];
$REQ->{whisker}->{port} = $ST[1];
$REQ->{whisker}->{lowercase_incoming_headers} = 1;
$REQ->{whisker}->{ignore_duplicate_headers}   = 0;
delete $REQ->{whisker}->{parameters};
http_fixup_request($REQ);
push @$Q, \@ST;
while (@$Q) {
@ST = @{ shift @$Q };
next if ( defined $TRACK->{ $ST[2] } && $TRACK->{ $ST[2] } ne '?' );
if ( $ST[3] > $C->{depth} ) {
$TRACK->{ $ST[2] } = '?' if ( $CONFIG->{save_skipped} > 0 );
next;
}
$ST[4] = uri_get_dir( $ST[2] );
$REQ->{whisker}->{uri} = $ST[2];
if ( $ST[5] ne '' && $CONFIG->{use_referrers} > 0 ) {
$REQ->{Referrer} = $ST[5];
}
my $result = _crawl_do_request( $REQ, $RESP, $C );
if ( $result == 1 || $result == 2 ) {
push @{ $C->{errors} }, "$ST[2]: $RESP->{whisker}->{error}";
next;
}
$COUNT++;
$TRACK->{ $ST[2] } = $RESP->{whisker}->{code}
if ( $result == 0 || $result == 4 );
$TRACK->{ $ST[2] } = '?'
if ( ( $result == 3 || $result == 5 )
&& $CONFIG->{save_skipped} > 0 );
if ( defined $RESP->{server} && !ref( $RESP->{server} ) ) {
$C->{server_tags}->{ $RESP->{server} }++;
}
if ( defined $RESP->{'set-cookie'} ) {
if ( $CONFIG->{save_cookies} > 0 ) {
if ( ref( $RESP->{'set-cookie'} ) ) {
$C->{cookies}->{$_}++
foreach ( @{ $RESP->{'set-cookie'} } );
}
else {
$C->{cookies}->{ $RESP->{'set-cookie'} }++;
}
}
cookie_read( $C->{jar}, $RESP )
if ( $CONFIG->{reuse_cookies} > 0 );
}
next if ( $result == 4 || $result == 5 );
next if ( scalar @$Q > $CONFIG->{url_limit} );
if ( $result == 0 ) {    # page should be parsed
if ( $CONFIG->{source_callback} != 0
&& ref( $CONFIG->{source_callback} ) eq 'CODE' )
{
&{ $CONFIG->{source_callback} }($C);
}
html_find_tags( \$RESP->{whisker}->{data},
\&_crawl_extract_links_test, 0, $C, \%_crawl_linktags );
$C->{parsed_page_count}++;
}
push @$URLS, $RESP->{location} if ( $result == 3 );
foreach $T (@$URLS) {
$T =~ tr/\0\r\n//d;
next if ( length($T) == 0 );
next if ( $T =~ /^#/i );       # fragment
push @{ $C->{referrers}->{$T} }, $ST[2]
if ( $CONFIG->{save_referrers} > 0 );
if (   $T =~ /^([a-zA-Z0-9]*):/
&& lc($1) ne 'http'
&& lc($1) ne 'https' )
{
push @{ $C->{non_http}->{$T} }, $ST[2]
if ( $CONFIG->{save_non_http} > 0 );
next;
}
if ( substr( $T, 0, 2 ) eq '//' && $CONFIG->{netloc_bug} > 0 ) {
if ( $REQ->{whisker}->{ssl} > 0 ) { $T = 'https:' . $T; }
else { $T = 'http:' . $T; }
}
if ( $CONFIG->{callback} != 0 ) {
next if &{ $CONFIG->{callback} }( $T, $C );
}
$T = uri_absolute( $T, $ST[4], $CONFIG->{normalize_uri} );
@v = uri_split($T);
if (   ( defined $v[2] && $v[2] ne $ST[0] )
|| ( $v[3] > 0 && $v[3] != $ST[1] ) )
{
$C->{offsites}->{ uri_join(@v) }++
if ( $CONFIG->{save_offsites} > 0 );
next;
}
if ( $v[0] =~ /\.([a-z0-9]+)$/i ) {
if ( defined $CONFIG->{skip_ext}->{ lc($1) } ) {
$TRACK->{ $v[0] } = '?'
if ( $CONFIG->{save_skipped} > 0 );
next;
}
}
if ( defined $v[4] && $CONFIG->{use_params} > 0 ) {
$TRACK->{ $v[0] } = '?'
if ( $CONFIG->{params_double_record} > 0
&& !defined $TRACK->{ $v[0] } );
$v[0] = $v[0] . '?' . $v[4];
}
next
if ( defined $TRACK->{ $v[0] } )
;    # we've processed this already
push @$Q, [ $ST[0], $ST[1], $v[0], $ST[3] + 1, '', $ST[2] ];
}    # foreach
@$URLS = ();    # reset for next round
}    # while
return $COUNT;
}    # end sub crawl
sub _crawl_extract_links_test {
my ( $TAG, $hr, $dr, $start, $len, $OBJ ) = ( lc(shift), @_ );
return undef if ( !scalar %$hr );    # fastpath quickie
my $t = $_crawl_linktags{$TAG};
while ( my ( $key, $val ) = each %$hr ) {    # normalize element values
$$hr{ lc($key) } = $val;
}
if (   $TAG eq 'meta'
&& defined $$hr{'http-equiv'}
&& $$hr{'http-equiv'} eq 'refresh'
&& defined $$hr{'content'}
&& $$hr{'content'} =~ m/url=(.+)/i )
{
push( @{ $OBJ->{urls} }, $1 );
}
elsif ( ref($t) ) {
foreach (@$t) {
push( @{ $OBJ->{urls} }, $$hr{$_} ) if ( defined $$hr{$_} );
}
}
else {
push( @{ $OBJ->{urls} }, $$hr{$t} ) if ( defined $$hr{$t} );
}
if ( $TAG eq 'form' && defined $$hr{action} ) {
my $u = $OBJ->{response}->{whisker}->{uri};
$OBJ->{forms}->{ uri_absolute( $$hr{action}, $u, 1 ) }++;
}
return undef;
}
sub _crawl_do_request_ex {
my ( $hrin, $hrout, $OBJ ) = @_;
my $ret;
$ret = http_do_request( $hrin, $hrout );
return ( 2, $ret )
if ( $ret == 2 );     # if there was connection error, do not continue
if   ( $ret == 0 ) {    # successful request
if (   $$hrout{whisker}->{code} < 308
&& $$hrout{whisker}->{code} > 300 )
{
if ( $OBJ->{config}->{follow_moves} > 0 ) {
return ( 3, $ret )
if ( defined $$hrout{location}
&& !ref( $$hrout{location} ) );
}
return ( 5, $ret );    # not avail
}
if ( $$hrout{whisker}->{code} == 200 ) {
if ( defined $$hrout{'content-type'}
&& $$hrout{'content-type'} !~ /^text\/htm/i )
{
return ( 4, $ret );
}
}
}
return ( -1, $ret );    # fallthrough
}
sub _crawl_do_request {
my ( $hrin, $hrout, $OBJ ) = @_;
my ( $cret, $lwret );
if ( $OBJ->{config}->{do_head} && $$hrin{whisker}->{method} ne 'HEAD' )
{
my $save = $$hrin{whisker}->{method};
$$hrin{whisker}->{method} = 'HEAD';
( $cret, $lwret ) = _crawl_do_request_ex( $hrin, $hrout, $OBJ );
$$hrin{whisker}->{method} = $save;
return $cret if ( $cret > 0 );
if ( $lwret == 0 ) {    # successful request
if ( $$hrout{whisker}->{code} == 501 ) {    # HEAD not allowed
$OBJ->{config}->{do_head} = 0;    # no more HEAD requests
}
}
}
( $cret, $lwret ) = _crawl_do_request_ex( $hrin, $hrout, $OBJ );
return $lwret if ( $cret < 0 );
return $cret;
}
}    # CRAWL_CONTAINER
sub dump {
my %what = @_;
my ( $final, $k, $v ) = ('');
while ( ( $k, $v ) = each %what ) {
return undef if ( ref($k) || !ref($v) );
$final .= "\$$k = " . _dump( 1, $v, 1 );
$final =~ s#,\n$##;
$final .= ";\n";
}
return $final;
}
sub dump_writefile {
my $file   = shift;
my $output = &dump(@_);
return 1 if ( !open( OUT, ">$file" ) || !defined $output );
binmode(OUT);
print OUT $output;
close(OUT);
}
sub _dump {    # dereference and dump an element
my ( $t,   $ref, $depth ) = @_;
my ( $out, $k,   $v )     = ('');
$depth ||= 1;
return 'undef' if ( $depth > 128 );
if ( !defined $ref ) {
return 'undef';
}
elsif ( ref($ref) eq 'HASH' ) {
$out .= "{\n";
while ( ( $k, $v ) = each %$ref ) {
$out .= "\t" x $t;
$out .= _dumpd($k) . ' => ';
if ( ref($v) ) { $out .= _dump( $t + 1, $v, $depth + 1 ); }
else { $out .= _dumpd($v); }
$out .= ",\n" unless ( substr( $out, -2, 2 ) eq ",\n" );
}
$out =~ s#,\n$#\n#;
$out .= "\t" x ( $t - 1 );
$out .= "},\n";
}
elsif ( ref($ref) eq 'ARRAY' ) {
$out .= "[";
if ( ~~@$ref ) {
$out .= "\n";
foreach $v (@$ref) {
$out .= "\t" x $t;
if ( ref($v) ) { $out .= _dump( $t + 1, $v, $depth + 1 ); }
else { $out .= _dumpd($v); }
$out .= ",\n" unless ( substr( $out, -2, 2 ) eq ",\n" );
}
$out =~ s#,\n$#\n#;
$out .= "\t" x ( $t - 1 );
}
$out .= "],\n";
}
elsif ( ref($ref) eq 'SCALAR' ) {
$out .= _dumpd($$ref);
}
elsif ( ref($ref) eq 'REF' ) {
$out .= _dump( $t, $$ref, $depth + 1 );
}
elsif ( ref($ref) ) {    # unknown/unsupported ref
$out .= "undef";
}
else {                   # normal scalar
$out .= _dumpd($ref);
}
return $out;
}
sub _dumpd {                 # escape a scalar string
my $v = shift;
return 'undef' if ( !defined $v );
return "''"    if ( $v eq '' );
return "$v"    if ( $v eq '0' || $v !~ tr/0-9//c && $v !~ m#^0+# );
if ( $v !~ tr/ !-~//c ) {
$v =~ s/(['\\])/\\$1/g;
return "'$v'";
}
$v =~ s#\\#\\\\#g;
$v =~ s#"#\\"#g;
$v =~ s#\r#\\r#g;
$v =~ s#\n#\\n#g;
$v =~ s#\t#\\t#g;
$v =~ s#\$#\\\$#g;
$v =~ s#([^!-~ ])#sprintf('\\x%02x',ord($1))#eg;
return "\"$v\"";
}
{    # package variables
my $MIMEBASE64_TRYLOADING = 1;
sub encode_base64 {
if ($MIMEBASE64_TRYLOADING) {
eval "require MIME::Base64";
$MIMEBASE64_TRYLOADING = 0;
}
goto &MIME::Base64::encode_base64 if ($MIME::Base64::VERSION);
my $res = "";
my $eol = $_[1];
$eol = "\n" unless defined $eol;
pos( $_[0] ) = 0;
while ( $_[0] =~ /(.{1,45})/gs ) {
$res .= substr( pack( 'u', $1 ), 1 );
chop($res);
}
$res =~ tr|` -_|AA-Za-z0-9+/|;
my $padding = ( 3 - length( $_[0] ) % 3 ) % 3;
$res =~ s/.{$padding}$/'=' x $padding/e if $padding;
if ( length $eol ) {
$res =~ s/(.{1,76})/$1$eol/g;
}
$res;
}
sub decode_base64 {
if ($MIMEBASE64_TRYLOADING) {
eval "require MIME::Base64";
$MIMEBASE64_TRYLOADING = 0;
}
goto &MIME::Base64::decode_base64 if ($MIME::Base64::VERSION);
my $str = shift;
my $res = "";
$str =~ tr|A-Za-z0-9+=/||cd;
$str =~ s/=+$//;                # remove padding
$str =~ tr|A-Za-z0-9+/| -_|;    # convert to uuencoded format
while ( $str =~ /(.{1,60})/gs ) {
my $len = chr( 32 + length($1) * 3 / 4 );    # compute length byte
$res .= unpack( "u", $len . $1 );            # uudecode
}
$res;
}
}    # end package variables
sub encode_uri_hex {    # normal hex encoding
my $str = shift;
$str =~ s/([^\/])/sprintf("%%%02x",ord($1))/ge;
return $str;
}
sub encode_uri_randomhex {    # random normal hex encoding
my @T = split( //, shift );
my $s;
foreach (@T) {
if (m#[;=:&@\?]#) {
$s .= $_;
next;
}
if ( ( rand() * 2 ) % 2 == 1 ) { $s .= sprintf( "%%%02x", ord($_) ); }
else { $s .= $_; }
}
return $s;
}
sub encode_uri_randomcase {
my ( $x, $uri ) = ( '', shift );
return $uri if ( $uri !~ tr/a-zA-Z// );    # fast-path
my @T = split( //, $uri );
for ( $x = 0 ; $x < ( scalar @T ) ; $x++ ) {
if ( ( rand() * 2 ) % 2 == 1 ) {
$T[$x] =~ tr/A-Za-z/a-zA-Z/;
}
}
return join( '', @T );
}
sub encode_unicode {
my ( $c, $r ) = ( '', '' );
foreach $c ( split( //, shift ) ) {
$r .= pack( "v", ord($c) );
}
return $r;
}
sub decode_unicode {
my $str = $_[0];
return $str if ( $str !~ tr/!-~//c );    # fastpath
my ( $lead, $count, $idx );
my $out = '';
my $len = length($str);
my ( $ptr, $no, $nu ) = ( 0, 0, 0 );
while ( $ptr < $len ) {
my $c = substr( $str, $ptr, 1 );
if ( ord($c) >= 0xc0 && ord($c) <= 0xfd ) {
$count = 0;
$c     = ord($c) << 1;
while ( ( $c & 0x80 ) == 0x80 ) {
$c <<= 1;
last if ( $count++ == 4 );
}
$c = ( $c & 0xff );
for ( $idx = 1 ; $idx < $count ; $idx++ ) {
my $o = ord( substr( $str, $ptr + $idx, 1 ) );
$no = 1 if ( $o != 0x80 );
$nu = 1 if ( $o < 0x80 || $o > 0xbf );
}
my $o = ord( substr( $str, $ptr + $idx, 1 ) );
$nu = 1 if ( $o < 0x80 || $o > 0xbf );
if ($nu) {
$out .= substr( $str, $ptr++, 1 );
}
else {
if ($no) {
$out .= "\xff";    # generic replacement char
}
else {
my $prior =
ord( substr( $str, $ptr + $count - 1, 1 ) ) << 6;
$out .= pack( "C",
(( ord( substr( $str, $ptr + $count, 1 ) ) & 0x7f ) +
$prior ) & 255 );
}
$ptr += $count + 1;
}
$no = $nu = 0;
}
else {
$out .= $c;
$ptr++;
}
}
return $out;
}
sub encode_anti_ids {
my ( $rhin, $modes ) = ( shift, shift );
my ( @T, $x, $c, $s, $y );
my $ENCODED = 0;
my $W       = $$rhin{'whisker'};
return if ( !( defined $rhin && ref($rhin) ) );
$$rhin{'whisker'}->{'uri_orig'} = $$rhin{'whisker'}->{'uri'};
if ( $modes =~ /4/ ) {
$s = '';
if ( $$W{'uri'} =~ m#^/# ) {
$y = &utils_randstr;
$s .= $y while ( length($s) < 512 );
$$W{'uri'} = "/$s/.." . $$W{'uri'};
}
}
if ( $modes =~ /7/ ) {
$$W{'uri'} = encode_uri_randomcase( $$W{'uri'} );
}
if ( $modes =~ /2/ ) {
$$W{'uri'} =~ s#/#/./#g;
}
if ( $modes =~ /8/ ) {
$$W{'uri'} =~ s#/#\\#g;
$$W{'uri'} =~ s#^\\#/#;
$$W{'uri'} =~ s#^([a-zA-Z0-9_]+):\\#$1://#;
$$W{'uri'} =~ s#\\$#/#;
}
if ( $modes =~ /1/ ) {
if ( $ENCODED == 0 ) {
$$W{'uri'} = encode_uri_randomhex( $$W{'uri'} );
$ENCODED = 1;
}
}
if ( $modes =~ /5/ ) {
( $s, $y ) = ( &utils_randstr, &utils_randstr );
$$W{'uri'} = "/$s.html%3F$y=/../$$W{'uri'}";
}
if ( $modes =~ /3/ ) {
$s = &utils_randstr;
$$W{'uri'} = "/%20HTTP/1.1%0d%0aAccept%3a%20$s/../..$$W{'uri'}";
}
if ( $modes =~ /6/ ) {
$$W{'http_space1'} = "\t";
}
if ( $modes =~ /A/i ) {
$$W{'http_space1'} = $$W{'http_space2'} = "\x0d";
}
if ( $modes =~ /B/i ) {
$$W{'http_space1'} = $$W{'http_space2'} = "\x0b";
}
}
%_forms_ELEMENTS = (
'form'     => 1,
'input'    => 1,
'textarea' => 1,
'button'   => 1,
'select'   => 1,
'option'   => 1,
'/select'  => 1
);
sub forms_read {
my $dr = shift;
return undef if ( !ref($dr) || length($$dr) == 0 );
my $A = [ {}, [] ];
html_find_tags( $dr, \&_forms_parse_callback, 0, $A, \%_forms_ELEMENTS );
if ( scalar %{ $A->[0] } ) {
push( @{ $A->[1] }, $A->[0] );
}
return $A->[1];
}
sub forms_write {
my $hr = shift;
return undef if ( !ref($hr) || !( scalar %$hr ) );
return undef if ( !defined $$hr{"\0"} );
my $t = '<form name="' . $$hr{"\0"}->[0] . '" method="';
$t .= $$hr{"\0"}->[1] . '" action="' . $$hr{"\0"}->[2] . '"';
if ( defined $$hr{"\0"}->[3] ) {
$t .= ' ' . join( ' ', @{ $$hr{"\0"}->[3] } );
}
$t .= ">\n";
my ( $name, $ar );
while ( ( $name, $ar ) = each(%$hr) ) {
next if ( $name eq "\0" );
next if ( $name eq '' && $ar->[0]->[0] eq '' );
foreach $a (@$ar) {
my $P = '';
$P = ' ' . join( ' ', @{ $$a[2] } ) if ( defined $$a[2] );
$t .= "\t";
if ( $$a[0] eq 'textarea' ) {
$t .= "<textarea name=\"$name\"$P>$$a[1]";
$t .= "</textarea>\n";
}
elsif ( $$a[0] =~ m/^input-(.+)$/ ) {
$t .= "<input type=\"$1\" name=\"$name\" ";
$t .= "value=\"$$a[1]\"$P>\n";
}
elsif ( $$a[0] eq 'option' ) {
$t .= "\t<option value=\"$$a[1]\"$P>$$a[1]\n";
}
elsif ( $$a[0] eq 'select' ) {
$t .= "<select name=\"$name\"$P>\n";
}
elsif ( $$a[0] eq '/select' ) {
$t .= "</select$P>\n";
}
else {    # button
$t .= "<button name=\"$name\" value=\"$$a[1]\">\n";
}
}
}
$t .= "</form>\n";
return $t;
}
{    # these are 'private' static variables for &_forms_parse_html
my $CURRENT_SELECT = undef;
my $UNKNOWNS       = 0;
sub _forms_parse_callback {
my ( $TAG, $hr, $dr, $start, $len, $ar ) = ( lc(shift), @_ );
my ( $saveparam, $parr, $key ) = ( 0, undef, '' );
my $_forms_CURRENT = $ar->[0];
my $_forms_FOUND   = $ar->[1];
if ( scalar %$hr ) {
while ( my ( $key, $val ) = each %$hr ) {
if ( $key =~ tr/A-Z// ) {
delete $$hr{$key};
if ( defined $val ) { $$hr{ lc($key) } = $val; }
else { $$hr{ lc($key) } = undef; }
}
}
}
if ( $TAG eq 'form' ) {
if ( scalar %$_forms_CURRENT ) {    # save last form
push( @$_forms_FOUND, $_forms_CURRENT );
$ar->[0] = {};
$_forms_CURRENT = $ar->[0];
}
$_forms_CURRENT->{"\0"} =
[ $$hr{name}, $$hr{method}, $$hr{action}, [] ];
delete $$hr{'name'};
delete $$hr{'method'};
delete $$hr{'action'};
$key      = "\0";
$UNKNOWNS = 0;
}
elsif ( $TAG eq 'input' ) {
$$hr{type}  = 'text'                  if ( !defined $$hr{type} );
$$hr{name}  = 'unknown' . $UNKNOWNS++ if ( !defined $$hr{name} );
$$hr{value} = undef                   if ( !defined $$hr{value} );
$key        = $$hr{name};
push @{ $_forms_CURRENT->{$key} },
[ 'input-' . $$hr{type}, $$hr{value}, [] ];
delete $$hr{'name'};
delete $$hr{'type'};
delete $$hr{'value'};
}
elsif ( $TAG eq 'select' ) {
$$hr{name} = 'unknown' . $UNKNOWNS++ if ( !defined $$hr{name} );
$key = $$hr{name};
push @{ $_forms_CURRENT->{$key} }, [ 'select', undef, [] ];
$CURRENT_SELECT = $key;
delete $$hr{name};
}
elsif ( $TAG eq '/select' ) {
push @{ $_forms_CURRENT->{$CURRENT_SELECT} },
[ '/select', undef, [] ];
$CURRENT_SELECT = undef;
return undef;
}
elsif ( $TAG eq 'option' ) {
return undef if ( !defined $CURRENT_SELECT );
if ( !defined $$hr{value} ) {
my $stop = index( $$dr, '<', $start + $len );
return undef if ( $stop == -1 );    # MAJOR PUKE
$$hr{value} =
substr( $$dr, $start + $len, ( $stop - $start - $len ) );
$$hr{value} =~ tr/\r\n//d;
}
push @{ $_forms_CURRENT->{$CURRENT_SELECT} },
[ 'option', $$hr{value}, [] ];
delete $$hr{value};
}
elsif ( $TAG eq 'textarea' ) {
my $stop = $start + $len;
$$hr{value} = $$hr{'='};
delete $$hr{'='};
$$hr{name} = 'unknown' . $UNKNOWNS++ if ( !defined $$hr{name} );
$key = $$hr{name};
push @{ $_forms_CURRENT->{$key} }, [ 'textarea', $$hr{value}, [] ];
delete $$hr{'name'};
delete $$hr{'value'};
}
else {    # button
$$hr{name}  = 'unknown' . $UNKNOWNS++ if ( !defined $$hr{name} );
$$hr{value} = undef                   if ( !defined $$hr{value} );
$key        = $$hr{name};
push @{ $_forms_CURRENT->{$key} }, [ 'button', $$hr{value}, [] ];
delete $$hr{'name'};
delete $$hr{'value'};
}
if ( scalar %$hr ) {
if ( $TAG eq 'form' ) { $parr = $_forms_CURRENT->{$key}->[3]; }
else {
$parr = $_forms_CURRENT->{$key}->[-1];
$parr = $parr->[2];
}
my ( $k, $v );
while ( ( $k, $v ) = each(%$hr) ) {
if ( defined $v ) { push @$parr, "$k=\"$v\""; }
else { push @$parr, $k; }
}
}
return undef;
}
}
{    # contained variables
$DR  = undef;    # data reference
$c   = 0;        # parser pointer
$LEN = 0;
sub html_find_tags {
my ( $dataref, $callbackfunc, $xml, $fref, $tagmap ) = @_;
return if ( !( defined $dataref      && ref($dataref) ) );
return if ( !( defined $callbackfunc && ref($callbackfunc) ) );
$xml ||= 0;
my ( $INTAG, $CURTAG, $LCCURTAG, $ELEMENT, $VALUE, $cc ) = (0);
my ( %TAG, $ret, $start, $tagstart, $tempstart, $x, $found );
my $usetagmap = ( ( defined $tagmap && ref($tagmap) ) ? 1 : 0 );
$CURTAG = $LCCURTAG = $ELEMENT = $VALUE = $cc = '';
$DR     = $dataref;
$LEN = length($$dataref);
for ( $c = 0 ; $c < $LEN ; $c++ ) {
$cc = substr( $$dataref, $c, 1 );
next if ( !$INTAG && $cc ne '>' && $cc ne '<' );
if ( $cc eq '<' ) {
if ($INTAG) {
$cc = '>';
$c--;
}
elsif ($xml
&& $LEN > ( $c + 9 )
&& substr( $$dataref, $c + 1, 8 ) eq '![CDATA[' )
{
$c += 9;
$tempstart = $c;
$found     = index( $$dataref, ']]>', $c );
$c         = $found + 2;
$c         = $LEN if ( $found < 0 );         # malformed XML
next;
}
elsif ( $LEN > ( $c + 3 )
&& substr( $$dataref, $c + 1, 3 ) eq '!--' )
{
$tempstart = $c;
$c += 4;
$found = index( $$dataref, '-->', $c );
if ( $found < 0 ) {
$found = index( $$dataref, '>', $c );
$found = $LEN if ( $found < 0 );
$c = $found;
}
else {
$c = $found + 2;
}
if ( $usetagmap == 0 || defined $tagmap->{'!--'} ) {
my $dat = substr(
$$dataref,
$tempstart + 4,
$found - $tempstart - 4
);
&$callbackfunc( '!--', { '=' => $dat },
$dataref, $tempstart, $c - $tempstart + 1, $fref );
}
next;
}
elsif ( !$INTAG ) {
next if ( substr( $$dataref, $c + 1, 1 ) =~ tr/ \t\r\n// );
$c++;
$INTAG    = 1;
$tagstart = $c - 1;
$CURTAG = '';
while ( $c < $LEN
&& ( $x = substr( $$dataref, $c, 1 ) ) !~
tr/ \t\r\n>=// )
{
$CURTAG .= $x;
$c++;
}
chop $CURTAG if ( $xml && substr( $CURTAG, -1, 1 ) eq '/' );
$c++ if ( defined $x && $x ne '>' );
$LCCURTAG = lc($CURTAG);
$INTAG = 0 if ( $LCCURTAG !~ tr/a-z0-9// );
next if ( $c >= $LEN );
$cc = substr( $$dataref, $c, 1 );
}
}
if ( $cc eq '>' ) {
next if ( !$INTAG );
if ( $LCCURTAG eq 'script' && !$xml ) {
$tempstart = $c + 1;
pos($$dataref) = $c;
if ( $$dataref !~ m#(</script.*?>)#ig ) {
}
else {
$c = pos($$dataref) - 1;
my $l = length($1);
$TAG{'='} =
substr( $$dataref, $tempstart,
$c - $tempstart - $l + 1 );
}
}
elsif ( $LCCURTAG eq 'textarea' && !$xml ) {
$tempstart = $c + 1;
pos($$dataref) = $c;
if ( $$dataref !~ m#(</textarea.*?>)#ig ) {
}
else {
$c = pos($$dataref) - 1;
my $l = length($1);
$TAG{'='} =
substr( $$dataref, $tempstart,
$c - $tempstart - $l + 1 );
}
}
$INTAG = 0;
$TAG{'/'}++
if ( $xml && substr( $$dataref, $c - 1, 1 ) eq '/' );
&$callbackfunc( $CURTAG, \%TAG, $dataref, $tagstart,
$c - $tagstart + 1, $fref )
if ( $usetagmap == 0 || defined $tagmap->{$LCCURTAG} );
$CURTAG = $LCCURTAG = '';
%TAG = ();
next;
}
if ($INTAG) {
$ELEMENT = '';
$VALUE   = undef;
pos($$dataref) = $c;
if ( $$dataref !~ m/[^ \t\r\n]/g ) {
$c = $LEN;
next;    # should we really abort?
}
$start = pos($$dataref) - 1;
if ( $$dataref !~ m/[ \t\r\n<>=]/g ) {
$c = $LEN;
next;    # should we really abort?
}
$c = pos($$dataref) - 1;
if ( $c > $start ) {
$ELEMENT = substr( $$dataref, $start, $c - $start );
chop $ELEMENT
if ( $xml && substr( $ELEMENT, -1, 1 ) eq '/' );
}
$cc = substr( $$dataref, $c, 1 );
if ( $cc ne '>' ) {
if ( $cc =~ tr/ \t\r\n// ) {
$c++
while ( substr( $$dataref, $c, 1 ) =~ tr/ \t\r\n// );
}
if ( substr( $$dataref, $c, 1 ) eq '=' ) {
$c++;
$start = $c;
my $p = substr( $$dataref, $c, 1 );
if ( $p eq '"' || $p eq '\'' ) {
$c++;
$start++;
$c = index( $$dataref, $p, $c );
if ( $c < 0 ) { $c = $LEN; next; }    # Bad HTML
$VALUE = substr( $$dataref, $start, $c - $start );
$c++;
pos($$dataref) = $c;
}
else {
pos($$dataref) = $c;
if ( $$dataref !~ /[ \t\r\n>]/g ) {
$c = $LEN;
}
else {
$c     = pos($$dataref) - 1;
$VALUE =
substr( $$dataref, $start, $c - $start );
chop $VALUE
if ( $xml
&& substr( $$dataref, $c - 1, 2 ) eq '/>' );
}
}
if ( substr( $$dataref, $c, 1 ) =~ tr/ \t\r\n// ) {
if ( $$dataref !~ /[^ \t\r\n]/g ) {
$c = $LEN;
next;    # should we really abort?
}
$c = pos($$dataref) - 1;
}
}
}    # if $c ne '>'
$c--;
$TAG{$ELEMENT} = $VALUE
if ( $ELEMENT ne '' || ( $xml && $ELEMENT ne '/' ) );
}
}
if ($INTAG) {
&$callbackfunc( $CURTAG, \%TAG, $dataref, $tagstart,
$c - $tagstart + 1, $fref )
if ( $usetagmap == 0 || defined $tagmap->{$LCCURTAG} );
}
$DR = undef;    # void dataref pointer
}
sub html_find_tags_rewrite {
return if ( !defined $DR );
my ( $pos, $len, $replace_str ) = @_;
substr( $$DR, $pos, $len ) = $replace_str;
my $l = ( length($replace_str) - $len );
$c   += $l;
$LEN += $l;
}
sub _html_find_tags_adjust {
my ( $p, $l ) = @_;
$c   += $p;
$LEN += $l;
}
}    # end container
sub html_link_extractor {
my $data = shift;
my $ptr;
if ( ref($data) ) {
$ptr = $data;
}
else {
$ptr = \$data;
}
my %OBJ = ( urls => [], forms => {} );
$OBJ{response}                   = {};
$OBJ{response}->{whisker}        = {};
$OBJ{response}->{whisker}->{uri} = '';
html_find_tags(
$ptr,                           # data
\&_crawl_extract_links_test,    # callback function
0,                              # xml mode
\%OBJ,                          # data object
\%_crawl_linktags
);                                  # tagmap
return @{ $OBJ{urls} };
}
%http_host_cache = ();
sub http_new_request {
my %X = @_;
my ( $k, $v, %RET, %RES );
http_init_request( \%RET );
while ( ( $k, $v ) = each(%X) ) {
$RET{whisker}->{$k} = $v;
}
$RES{whisker}          = {};
$RES{whisker}->{MAGIC} = 31340;
$RES{whisker}->{uri}   = '';
return ( \%RET, \%RES ) if wantarray();
return \%RET;
}
sub http_new_response {
my %RET;
$RET{whisker}          = {};
$RET{whisker}->{MAGIC} = 31340;
$RET{whisker}->{uri}   = '';
return \%RET;
}
sub http_init_request {    # doesn't return anything
my ($hin) = shift;
return if ( !( defined $hin && ref($hin) ) );
%$hin = ();            # clear control hash
$$hin{whisker} = {
http_space1                   => ' ',
http_space2                   => ' ',
version                       => '1.1',
method                        => 'GET',
protocol                      => 'HTTP',
port                          => 80,
uri                           => '/',
uri_prefix                    => '',
uri_postfix                   => '',
uri_param_sep                 => '?',
host                          => 'localhost',
timeout                       => 10,
include_host_in_uri           => 0,
ignore_duplicate_headers      => 1,
normalize_incoming_headers    => 1,
lowercase_incoming_headers    => 0,
require_newline_after_headers => 0,
invalid_protocol_return_value => 1,
ssl                           => 0,
ssl_save_info                 => 0,
http_eol                      => "\x0d\x0a",
force_close                   => 0,
force_open                    => 0,
retry                         => 1,
trailing_slurp                => 0,
force_bodysnatch              => 0,
max_size                      => 0,
MAGIC                         => 31339
};
$$hin{'Connection'} = 'Keep-Alive';
$$hin{'User-Agent'} = "Mozilla (libwhisker/$LW2::VERSION)";
}
sub http_do_request {
my ( $hin, $hout ) = ( shift, shift );
return 2 if ( !( defined $hin  && ref($hin) ) );
return 2 if ( !( defined $hout && ref($hout) ) );
%$hout                     = ();
$$hout{whisker}            = {};
$$hout{whisker}->{'MAGIC'} = 31340;
$$hout{whisker}->{uri}     = $$hin{whisker}->{uri};
if (   !defined $$hin{whisker}
|| !defined $$hin{whisker}->{'MAGIC'}
|| $$hin{whisker}->{'MAGIC'} != 31339 )
{
$$hout{whisker}->{error} = 'Input hash not initialized';
return 2;
}
if ( defined $_[0] ) {    # handle extra params
my %hashref;
if ( ref( $_[0] ) eq 'HASH' ) { %hashref = %{ $_[0] }; }
else { %hashref = @_; }
$$hin{whisker}->{$_} = $hashref{$_} foreach ( keys %hashref );
}
if ( defined $$hin{whisker}->{'anti_ids'} ) {    # handle anti_ids
my %copy = %$hin;
$copy{whisker} = {};
%{ $copy{whisker} } = %{ $$hin{whisker} };
encode_anti_ids( \%copy, $$hin{whisker}->{'anti_ids'} );
$hin = \%copy;
}
my $cache_key = stream_key($hin);
my $stream;
if ( !defined $http_host_cache{$cache_key} ) {
$stream = stream_new($hin);
$http_host_cache{$cache_key} = $stream;
}
else {
$stream = $http_host_cache{$cache_key};
}
if ( !defined $stream ) {
$$hout{whisker}->{error} = 'unable to allocate stream';
return 2;
}
my $retry_count = $$hin{whisker}->{retry};
my $puke_flag   = 0;
my $ret         = 1;
do {    # retries wrapper
my ( $aret, $pass );
if ( !$stream->{valid}->() ) {
$stream->{clearall}->();
if ( !$stream->{open}->($hin) ) {
$$hout{whisker}->{error} =
'opening stream: ' . $stream->{error};
$$hout{whisker}->{error} .=
'(reconnect problem after prior request)'
if ($puke_flag);
return 2;
}
if (   defined $$hin{whisker}->{proxy_host}
&& defined $$hin{whisker}->{auth_proxy_callback} )
{
$aret =
$$hin{whisker}->{auth_proxy_callback}
->( $stream, $hin, $hout );
return $aret if ( $aret != 0 );    # proxy auth error
}
if ( defined $$hin{whisker}->{auth_callback} ) {
$aret =
$$hin{whisker}->{auth_callback}->( $stream, $hin, $hout );
return 0     if ( $aret == 200 );    # auth not needed?
return $aret if ( $aret != 0 );      # auth error
}
}
_ssl_save_info( $hout, $stream )
if ( $$hin{whisker}->{ssl} > 0
&& $$hin{whisker}->{ssl_save_info} > 0 );
$ret = _http_do_request_ex( $stream, $hin, $hout );
$puke_flag++
if ( $ret == 1 && defined( $$hout{whisker}->{http_data_sent} ) );
return $ret
if ( $ret == 0 || $ret == 2 );    # success or fatal socket error
$retry_count--;
} while ( $retry_count >= 0 );
return $ret;
}
sub _http_do_request_ex {
my ( $stream, $hin, $hout, $raw ) = @_;
return 2 if ( !defined $stream );
return 2 if ( !( defined $hin && ref($hin) ) );
return 2 if ( !( defined $hout && ref($hout) ) );
my $W = $hin->{whisker};
if ( !defined $$hout{whisker}->{MAGIC}
|| $$hout{whisker}->{MAGIC} != 31340 )
{
%$hout                     = ();
$$hout{whisker}            = {};
$$hout{whisker}->{'MAGIC'} = 31340;
$$hout{whisker}->{uri}     = $$hin{whisker}->{uri};
}
$stream->{clear}->();
if ( defined $raw && ref($raw) ) {
$stream->{queue}->($$raw);
}
else {
$stream->{queue}->( http_req2line($hin) );
if ( $$W{version} ne '0.9' ) {
$stream->{queue}->( http_construct_headers($hin) );
$stream->{queue}->( $$W{raw_header_data} )
if ( defined $$W{raw_header_data} );
$stream->{queue}->( $$W{http_eol} );
$stream->{queue}->( $$W{data} ) if ( defined $$W{data} );
}    # http 0.9 support
}
if ( defined $$W{request_fingerprint} ) {
$$hout{whisker}->{request_fingerprint} =
'md5:' . md5( $stream->{bufout} )
if ( $$W{request_fingerprint} eq 'md5' );
$$hout{whisker}->{request_fingerprint} =
'md4:' . md4( $stream->{bufout} )
if ( $$W{request_fingerprint} eq 'md4' );
}
if ( !$stream->{'write'}->() ) {
$$hout{whisker}->{'error'} = 'sending request: ' . $stream->{error};
$stream->{'close'}->();
return 1;
}
$$hout{whisker}->{http_data_sent} = 1;
$$hout{whisker}->{'lowercase_incoming_headers'} =
$$W{'lowercase_incoming_headers'};
my @H;
if ( $$W{'version'} ne '0.9' ) {
do {    # catch '100 Continue' responses
my $resp = _http_getline($stream);
if ( !defined $resp ) {
$$hout{whisker}->{error} = 'error reading HTTP response';
$$hout{whisker}->{data}  = $stream->{bufin};
$stream->{'close'}->();
return 1;
}
$$hout{whisker}->{'raw_header_data'} .= $resp
if ( defined $$W{'save_raw_headers'} );
if ( $resp !~
/^([^\/]+)\/(\d\.\d)([ \t]+)(\d+)([ \t]*)(.*?)([\r\n]+)/ )
{
$$hout{whisker}->{'error'} = 'invalid HTTP response';
$$hout{whisker}->{'data'}  = $resp;
while ( defined( $_ = _http_getline($stream) ) ) {
$$hout{whisker}->{'data'} .= $_;
}
$stream->{'close'}->();
return $$W{'invalid_protocol_return_value'} || 1;
}
$$hout{whisker}->{protocol}    = $1;
$$hout{whisker}->{version}     = $2;
$$hout{whisker}->{http_space1} = $3;
$$hout{whisker}->{code}        = $4;
$$hout{whisker}->{http_space2} = $5;
$$hout{whisker}->{message}     = $6;
$$hout{whisker}->{http_eol}    = $7;
$$hout{whisker}->{'100_continue'}++ if ( $4 == 100 );
@H = http_read_headers( $stream, $hin, $hout );
if ( !$H[0] ) {
$$hout{whisker}->{'error'} =
'Error in reading headers: ' . $H[1];
$stream->{'close'}->();
return 1;
}
if ( !defined $H[3] ) {    # connection
my ($t) = utils_find_lowercase_key( $hin, 'connection' );
$H[3] = $t || 'close';
}
} while ( $$hout{whisker}->{'code'} == 100 );
}
else {    # http ver 0.9, we need to fake it since headers are not sent
$$hout{whisker}->{version}      = '0.9';
$$hout{whisker}->{code}         = 200;
$$hout{whisker}->{message} 	= '';
$H[3]                           = 'close';
}
if ( $$hout{whisker}->{code}==404 && defined $$W{'shortcut_on_404'} ) {
$stream->{'close'}->();
}
elsif ( defined $$W{data_sock} ) {
$$hout{whisker}->{data_sock}   = $stream->{sock};
$$hout{whisker}->{data_stream} = $stream;
}
else {
if (
$$W{'force_bodysnatch'}
|| (   $$W{'method'} ne 'HEAD'
&& $$hout{whisker}->{'code'} != 206
&& $$hout{whisker}->{'code'} != 102 )
)
{
return 1
if ( !http_read_body( $stream, $hin, $hout, $H[1], $H[2] ) );
if (   lc( $H[1] ) eq 'chunked'
&& defined $$hin{whisker}->{hide_chunked_responses}
&& $$hin{whisker}->{hide_chunked_responses} == 1
&& !defined $$hin{whisker}->{save_raw_chunks} )
{
$$hout{'Content-Length'} = length( $$hout{whisker}->{data} );
utils_delete_lowercase_key( $hout, 'transfer-encoding' );
my $new = [];
my $cl  = 0;
foreach ( @{ $$hout{whisker}->{header_order} } ) {
my $l = lc($_);
if ( $l eq 'content-length' ) {
$cl++;
next if ( $cl > 1 );
}
push @$new, $_ if ( $l ne 'transfer-encoding' );
}
push @$new, 'Content-Length' if ( $cl == 0 );
$$hout{whisker}->{header_order} = $new;
}
}
my ($ch) = LW2::utils_find_lowercase_key( $hin, 'connection' );
my $cl = 0;
$cl++
if (
(
lc( $H[3] ) ne 'keep-alive' || ( defined $ch
&& $ch =~ m/close/i )
)
&& $$W{'force_open'} != 1
);
$cl++ if ( $$W{'force_close'} > 0 || $stream->{forceclose} > 0 );
$cl++ if ( $$W{'ssl'} > 0 && $LW_SSL_KEEPALIVE == 0 );
$stream->{'close'}->() if ($cl);
}
if ( defined $$W{'header_delete_on_success'}
&& ref( $$W{'header_delete_on_success'} ) )
{
foreach ( @{ $$W{'header_delete_on_success'} } ) {
delete $hin->{$_} if ( exists $hin->{$_} );
}
delete $$W{header_delete_on_success};
}
$stream->{reqs}++;
$$hout{whisker}->{'stats_reqs'}   = $stream->{reqs};
$$hout{whisker}->{'stats_syns'}   = $stream->{syns};
$$hout{whisker}->{'socket_state'} = $stream->{state};
delete $$hout{whisker}->{'error'};    # no error
return 0;
}
sub http_req2line {
my ( $S, $hin, $UO ) = ( '', @_ );
$UO ||= 0;
if ( defined $$hin{whisker}->{'full_request_override'} ) {
return $$hin{whisker}->{'full_request_override'};
}
else {    # notice the components of a request--this is for flexibility
if ( $UO != 1 ) {
$S .= $$hin{whisker}->{'method'} . $$hin{whisker}->{'http_space1'};
if ( $$hin{whisker}->{'include_host_in_uri'} > 0 ) {
if ( $$hin{whisker}->{'ssl'} == 1 ) {
$S .= 'https://';
}
else {
$S .= 'http://';
}
if ( defined $$hin{whisker}->{'uri_user'} ) {
$S .= $$hin{whisker}->{'uri_user'};
if ( defined $$hin{whisker}->{'uri_password'} ) {
$S .= ':' . $$hin{whisker}->{'uri_password'};
}
$S .= '@';
}
$S .= $$hin{whisker}->{'host'} . ':' . $$hin{whisker}->{'port'};
}
}
$S .=
$$hin{whisker}->{'uri_prefix'}
. $$hin{whisker}->{'uri'}
. $$hin{whisker}->{'uri_postfix'};
if ( defined $$hin{whisker}->{'parameters'}
&& $$hin{whisker}->{'parameters'} ne '' )
{
$S .=
$$hin{whisker}->{'uri_param_sep'}
. $$hin{whisker}->{'parameters'};
}
if ( $UO != 1 ) {
if ( $$hin{whisker}->{'version'} ne '0.9' ) {
$S .=
$$hin{whisker}->{'http_space2'}
. $$hin{whisker}->{'protocol'} . '/'
. $$hin{whisker}->{'version'};
}
$S .= $$hin{whisker}->{'http_eol'};
}
}
return $S;
}
sub http_resp2line {
my $hout = shift;
my $out  = '';
return undef if ( !defined $hout || !ref($hout) );
return undef if ( $hout->{whisker}->{MAGIC} != 31340 );
$out .= $$hout{whisker}->{protocol};
$out .= '/';
$out .= $$hout{whisker}->{version};
$out .= $$hout{whisker}->{http_space1};
$out .= $$hout{whisker}->{code};
$out .= $$hout{whisker}->{http_space2};
$out .= $$hout{whisker}->{message};
$out .= $$hout{whisker}->{http_eol};
return $out;
}
sub _http_getline {
my $stream = shift;
my ( $str, $t, $bc ) = ( '', 0, 0 );
$t = index( $stream->{bufin}, "\n", 0 );
while ( $t < 0 ) {
return undef if !$stream->{read}->() || 
length($stream->{bufin}) == $bc;
$t = index( $stream->{bufin}, "\n", 0 );
$bc = length( $stream->{bufin} );
}
my $r = substr( $stream->{bufin}, 0, $t + 1 );
$stream->{bufin} = substr( $stream->{bufin}, $t + 1 );
return $r;
}
sub _http_get {    # read from socket w/ timeouts
my ( $stream, $amount ) = @_;
my ( $str, $t, $b )     = ( '', '', 0 );
while ( $amount > length( $stream->{bufin} ) ) {
return undef if !$stream->{read}->() ||
length( $stream->{bufin} ) == $b;
$b = length( $stream->{bufin} );
}
my $r = substr( $stream->{bufin}, 0, $amount );
$stream->{bufin} = substr( $stream->{bufin}, $amount );
return $r;
}
sub _http_getall {
my ( $tmp, $b, $stream, $max_size ) = ('', 0, @_);
while ( $stream->{read}->() && length( $stream->{bufin} ) != $b) {
last if ( $max_size && length( $stream->{bufin} ) >= $max_size );
$b = length( $stream->{bufin} );	
}
( $tmp, $stream->{bufin} ) = ( $stream->{bufin}, '' );
$tmp = substr($tmp, 0, $max_size) if($max_size && 
length($tmp) > $max_size);
return $tmp;
}
sub http_fixup_request {
my $hin = shift;
return if ( !( defined $hin && ref($hin) ) );
$$hin{whisker}->{uri} = '/' if ( $$hin{whisker}->{uri} eq '' );
$$hin{whisker}->{http_space1}= ' ';
$$hin{whisker}->{http_space2}= ' ';
$$hin{whisker}->{protocol}= 'HTTP';
$$hin{whisker}->{uri_param_sep}= '?';
if ( $$hin{whisker}->{'version'} eq '1.1' ) {
my ($host) = utils_find_lowercase_key($hin,'host');
$$hin{'Host'} = $$hin{whisker}->{'host'} 
if(!defined $host || $host eq '');
$$hin{'Host'} .= ':' . $$hin{whisker}->{'port'}
if ( index($$hin{'Host'},':') == -1 && 
( $$hin{whisker}->{port} != 80 || ( $$hin{whisker}->{ssl}==1 &&
$$hin{whisker}->{port} != 443 ) ) );
my ($conn) = utils_find_lowercase_key($hin,'connection');
$$hin{'Connection'} = 'Keep-Alive' 
if(!defined $conn || $conn eq '');
} elsif( $$hin{whisker}->{'version'} eq '1.0' ){
my ($conn) = utils_find_lowercase_key($hin,'connection');
$$hin{'Connection'} = 'close' 
if(!defined $conn || $conn eq '');
}
utils_delete_lowercase_key( $hin, 'content-length' );
if ( $$hin{whisker}->{method} eq 'POST' || 
defined $$hin{whisker}->{data} ) {
$$hin{whisker}->{data}||='';
$$hin{'Content-Length'} = length( $$hin{whisker}->{'data'} );
my ($v) = utils_find_lowercase_key( $hin, 'content-type' );
if ( !defined $v || $v eq '' ) {
$$hin{'Content-Type'} = 'application/x-www-form-urlencoded';
}
}
if ( defined $$hin{whisker}->{'proxy_host'} ) {
$$hin{whisker}->{'include_host_in_uri'} = 1;
}
}
sub http_reset {
my $stream;
foreach $stream ( keys %http_host_cache ) {
$stream->{'close'}->() if(ref($stream));
delete $http_host_cache{$stream};
}
}
sub ssl_is_available {
return 0 if ( $LW_SSL_LIB == 0 );
if ( $LW_SSL_LIB == 1 ) {
return 1 if ( !wantarray() );
return ( 1, "Net::SSLeay", $Net::SSLeay::VERSION );
}
elsif ( $LW_SSL_LIB == 2 ) {
return 1 if ( !wantarray() );
return ( 1, "Net::SSL", $Net::SSL::VERSION );
}
else {
utils_carp('',"ssl_is_available: sanity check failed");
return 0;
}
}
sub _ssl_save_info {
my ( $hr, $stream ) = @_;
my $cert;
if ( $stream->{streamtype} == 4 ) {
my $SSL = $stream->{sock};
$hr->{whisker}->{ssl_cipher} = Net::SSLeay::get_cipher($SSL);
if ( $cert = Net::SSLeay::get_peer_certificate($SSL) ) {
$hr->{whisker}->{ssl_cert_subject} =
Net::SSLeay::X509_NAME_oneline(
Net::SSLeay::X509_get_subject_name($cert) );
$hr->{whisker}->{ssl_cert_issuer} =
Net::SSLeay::X509_NAME_oneline(
Net::SSLeay::X509_get_issuer_name($cert) );
}
return;
}
if ( $stream->{streamtype} == 5 ) {
$hr->{whisker}->{ssl_cipher} = $stream->{sock}->get_cipher();
if ( $cert = $stream->{sock}->get_peer_certificate() ) {
$hr->{whisker}->{ssl_cert_subject} = $cert->subject_name();
$hr->{whisker}->{ssl_cert_issuer}  = $cert->issuer_name();
}
return;
}
}
sub http_read_headers {
my ( $stream, $in, $hout ) = @_;
my $W = $in->{whisker};
my ( $a, $b, $LC, $CL, $TE, $CO );
my $last;
pos( $stream->{bufin} ) = 0;
while (1) {
$last = pos( $stream->{bufin} );
if ( $stream->{bufin} !~ m/(.*?)[\r]{0,1}\n/g ) {
if ( !$stream->{read}->() ) {
last
if ( $$W{require_newline_after_headers} == 0
&& length( $stream->{bufin} ) - 1 == $last );
return ( 0, 'error reading in all headers' );
}
pos( $stream->{bufin} ) = $last;
next;
}
last if ( $1 eq '' );
return ( 0, 'malformed header' )
if ( $1 !~ m/^([^:]+):([ \t]*)(.*)$/ );
$$hout{whisker}->{'abnormal_header_spacing'}++ if ( $2 ne ' ' );
$a  = $1;
$b  = $3;
$LC = lc($a);
next if ( $LC eq 'whisker' );
$TE = lc($b) if ( $LC eq 'transfer-encoding' );
$CL = $b     if ( $LC eq 'content-length' );
$CO = lc($b) if ( $LC eq 'connection' );
push( @{ $$hout{whisker}->{cookies} }, $b )
if ( $LC eq 'set-cookie' || $LC eq 'set-cookie2' );
if ( $$W{'lowercase_incoming_headers'} > 0 ) {
$a = $LC;
}
elsif ( $$W{'normalize_incoming_headers'} > 0 ) {
$a = ucfirst($LC);
$a = 'ETag' if ( $a eq 'Etag' );
$a =~ s/(-[a-z])/uc($1)/eg;
}
push( @{ $$hout{whisker}->{header_order} }, $a );
if ( defined $$hout{$a} && $$W{ignore_duplicate_headers} != 1 ) {
$$hout{$a} = [ $$hout{$a} ] if ( !ref( $$hout{$a} ) );
push( @{ $$hout{$a} }, $b );
}
else {
$$hout{$a} = $b;
}
}
my $found = pos( $stream->{bufin} );
$$hout{whisker}->{'raw_header_data'} = substr( $stream->{bufin}, 0, $found )
if ( defined $$W{'save_raw_headers'} );
$stream->{bufin} = substr( $stream->{bufin}, $found );
return ( 1, $TE, $CL, $CO );
}
sub http_read_body {
my ( $temp, $stream, $hin, $hout, $enc, $len ) = ( '', @_ );
my $max_size = $hin->{whisker}->{max_size} || 0;
$$hout{whisker}->{data} = '';
if ( defined $enc && lc($enc) eq 'chunked' ) {
my $total = 0;
my $x;
my $saveraw = $$hin{whisker}->{save_raw_chunks} || 0;
if ( !defined( $x = _http_getline($stream) ) ) {
$$hout{whisker}->{'error'} = 'Error reading chunked data length';
$stream->{'close'}->();
return 0;
}
$a = $x;
$a =~ tr/a-fA-F0-9//cd;
if ( length($a) > 8 ) {
$$hout{whisker}->{'error'} = 'Chunked size is too big: ' . $x;
$stream->{'close'}->();
return 0;
}
$len = hex($a);
$len = $max_size if ( $max_size && $len > $max_size );
$$hout{whisker}->{'data'} = $x if ($saveraw);
while ( $len > 0 ) {    # chunked sucks
if ( !defined( $temp = _http_get( $stream, $len ) ) ) {
$$hout{whisker}->{'error'} = 'Error reading chunked data';
$stream->{'close'}->();
return 0;
}
$$hout{whisker}->{'data'} = $$hout{whisker}->{'data'} . $temp;
$total += $len;
if ( $max_size && $total >= $max_size ) {
$stream->{'close'}->();
return 1;
}
$temp = _http_getline($stream);
$$hout{whisker}->{'data'} .= $temp if ( $saveraw && defined $temp );
if ( defined $temp && $temp =~ /^[\r\n]*$/ ) {
$temp = _http_getline($stream);
$$hout{whisker}->{'data'} .= $temp
if ( $saveraw && defined $temp );
}
if ( !defined $temp ) {
$$hout{whisker}->{'error'} = 'Error reading chunked data';
$stream->{'close'}->();
return 0;
}
$temp =~ tr/a-fA-F0-9//cd;
if ( length($temp) > 8 ) {
$$hout{whisker}->{'error'} =
'Chunked size is too big: ' . $temp;
$stream->{'close'}->();
return 0;
}
$len = hex($temp);
$len = ( $max_size - $total )
if ( $max_size && $len > ( $max_size - $total ) );
}
while ( defined( $_ = _http_getline($stream) ) ) {
$$hout{whisker}->{'data'} .= $_ if ($saveraw);
tr/\r\n//d;
last if ( $_ eq '' );
}
}
else {
if ( defined $len ) {
return 1 if ( $len <= 0 );
$len = $max_size if ( $max_size && $len > $max_size );
if (
!defined(
$$hout{whisker}->{data} = _http_get( $stream, $len )
)
)
{
$stream->{'close'}->();
my $s = $$hin{whisker}->{allow_short_reads} || 0;
if ( $s != 0 && length($stream->{'bufin'}) > 0 ) {
$$hout{whisker}->{'data'} = $stream->{'bufin'};
return 1;
}
$$hout{whisker}->{'error'} =
'Error reading data: ' . $stream->{error};
return 0;
}
}
else {    # Yuck...read until server stops sending....
$$hout{whisker}->{data} = _http_getall( $stream, $max_size );
$stream->{'close'}->();
}
$$hout{whisker}->{'data'} ||= '';
}
return 1;
}
sub http_construct_headers {
my $hin = shift;
my ( %SENT, $output, $i );
my $EOL = $hin->{whisker}->{http_eol} || "\x0d\x0a";
if ( defined $hin->{whisker}->{header_order}
&& ref( $hin->{whisker}->{header_order} ) eq 'ARRAY' )
{
foreach ( @{ $hin->{whisker}->{header_order} } ) {
next if ( $_ eq '' || $_ eq 'whisker' || !defined $hin->{$_} );
if ( ref( $hin->{$_} ) ) {
utils_croak("http_construct_headers: non-array header value reference")
if ( ref( $hin->{$_} ) ne 'ARRAY' );
$SENT{$_} ||= 0;
my $v = $$hin{$_}->[ $SENT{$_} ];
$output .= "$_: $v$EOL";
}
else {
$output .= "$_: $$hin{$_}$EOL";
}
$SENT{$_}++;
}
}
foreach ( keys %$hin ) {
next if ( $_ eq '' || $_ eq 'whisker' );
if ( ref( $hin->{$_} ) ) {    # header with multiple values
utils_croak("http_construct_headers: non-array header value ref") 
if ( ref( $hin->{$_} ) ne 'ARRAY' );
$SENT{$_} ||= 0;
for($i=$SENT{$_}; $i<~~@{ $hin->{$_} }; $i++) {
$output .= "$_: " . $hin->{$_}->[$i] . $EOL;
}
}
else {                       # normal header
next if ( defined $SENT{$_} );
$output .= "$_: $$hin{$_}$EOL";
}
}
return $output;
}
sub http_close {
my $hin       = shift;
my $cache_key = stream_key($hin);
return if ( !defined $http_host_cache{$cache_key} );
my $stream = $http_host_cache{$cache_key};
$stream->{'close'}->();
}
sub http_do_request_timeout {
my ( $req, $resp, $timeout ) = @_;
$timeout ||= 30;
my $result;
eval {
local $SIG{ALRM} = sub { die "timeout\n" };
eval { alarm($timeout) };
$result = LW2::http_do_request( $req, $resp );
eval { alarm(0) };
};
if ($@) {
$result                   = 1;
$resp->{whisker}->{error} = 'Error with timeout wrapper';
$resp->{whisker}->{error} = 'Total transaction timed out'
if ( $@ =~ /timeout/ );
}
return $result;
}
{    # start md5 packaged varbs
my ( @S, @T, @M );
my $code           = '';
my $MD5_TRYLOADING = 1;
sub md5 {
return undef if ( !defined $_[0] );    # oops, forgot the data
if ($MD5_TRYLOADING) {
$MD5_TRYLOADING = 0;
eval "require MD5";
}
return MD5->hexhash( $_[0] ) if ($MD5::VERSION);
my $DATA = _md5_pad( $_[0] );
&_md5_init() if ( !defined $M[0] );
return _md5_perl_generated( \$DATA );
}
sub _md5_init {
return if ( defined $S[0] );
my $i;
for ( $i = 1 ; $i <= 64 ; $i++ ) {
$T[ $i - 1 ] = int( ( 2**32 ) * abs( sin($i) ) );
}
my @t = ( 7, 12, 17, 22, 5, 9, 14, 20, 4, 11, 16, 23, 6, 10, 15, 21 );
for ( $i = 0 ; $i < 64 ; $i++ ) {
$S[$i] = $t[ ( int( $i / 16 ) * 4 ) + ( $i % 4 ) ];
}
@M = (
0, 1, 2,  3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 13, 14, 15,
1, 6, 11, 0,  5,  10, 15, 4,  9,  14, 3,  8,  13, 2,  7,  12,
5, 8, 11, 14, 1,  4,  7,  10, 13, 0,  3,  6,  9,  12, 15, 2,
0, 7, 14, 5,  12, 3,  10, 1,  8,  15, 6,  13, 4,  11, 2,  9
);
&_md5_generate();
my $TEST = _md5_pad('foobar');
if ( _md5_perl_generated( \$TEST ) ne
'3858f62230ac3c915f300c664312c63f' )
{
utils_carp('md5: MD5 self-test not successful.');
}
}
sub _md5_pad {
my $l = length( my $msg = shift() . chr(128) );
$msg .= "\0" x ( ( $l % 64 <= 56 ? 56 : 120 ) - $l % 64 );
$l = ( $l - 1 ) * 8;
$msg .= pack 'VV', $l & 0xffffffff, ( $l >> 16 >> 16 );
return $msg;
}
sub _md5_generate {
my $N = 'abcddabccdabbcda';
my ( $i, $M ) = ( 0, '' );
$M = '&0xffffffff' if ( ( 1 << 16 ) << 16 );    # mask for 64bit systems
$code = <<EOT;
sub _md5_perl_generated {
BEGIN { \$^H |= 1; }; # use integer
my (\$A,\$B,\$C,\$D)=(0x67452301,0xefcdab89,0x98badcfe,0x10325476);
my (\$a,\$b,\$c,\$d,\$t,\$i);
my \$dr=shift;
my \$l=length(\$\$dr);
for my \$L (0 .. ((\$l/64)-1) ) {
my \@D = unpack('V16', substr(\$\$dr, \$L*64,64));
(\$a,\$b,\$c,\$d)=(\$A,\$B,\$C,\$D);
EOT
for ( $i = 0 ; $i < 16 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .=
"\$t=((\$$d^(\$$b\&(\$$c^\$$d)))+\$$a+\$D[$M[$i]]+$T[$i])$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1)))+\$$b)$M;\n";
}
for ( ; $i < 32 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .=
"\$t=((\$$c^(\$$d\&(\$$b^\$$c)))+\$$a+\$D[$M[$i]]+$T[$i])$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1)))+\$$b)$M;\n";
}
for ( ; $i < 48 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .= "\$t=((\$$b^\$$c^\$$d)+\$$a+\$D[$M[$i]]+$T[$i])$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1)))+\$$b)$M;\n";
}
for ( ; $i < 64 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .= "\$t=((\$$c^(\$$b|(~\$$d)))+\$$a+\$D[$M[$i]]+$T[$i])$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1)))+\$$b)$M;\n";
}
$code .= <<EOT;
\$A=\$A+\$a\&0xffffffff; \$B=\$B+\$b\&0xffffffff;
\$C=\$C+\$c\&0xffffffff; \$D=\$D+\$d\&0xffffffff;
} # for
return unpack('H*', pack('V4',\$A,\$B,\$C,\$D)); }
EOT
eval "$code";
}
}    # md5 package container
{    # start md4 packaged varbs
my ( @S, @T, @M );
my $code = '';
sub md4 {
return undef if ( !defined $_[0] );    # oops, forgot the data
my $DATA = _md5_pad( $_[0] );
&_md4_init() if ( !defined $M[0] );
return _md4_perl_generated( \$DATA );
}
sub _md4_init {
return if ( defined $S[0] );
my $i;
my @t = ( 3, 7, 11, 19, 3, 5, 9, 13, 3, 9, 11, 15 );
for ( $i = 0 ; $i < 48 ; $i++ ) {
$S[$i] = $t[ ( int( $i / 16 ) * 4 ) + ( $i % 4 ) ];
}
@M = (
0, 1, 2, 3,  4, 5,  6, 7,  8, 9, 10, 11, 12, 13, 14, 15,
0, 4, 8, 12, 1, 5,  9, 13, 2, 6, 10, 14, 3,  7,  11, 15,
0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5,  13, 3,  11, 7,  15
);
my $N = 'abcddabccdabbcda';
my $M = '';
$M = '&0xffffffff' if ( ( 1 << 16 ) << 16 );    # mask for 64bit systems
$code = <<EOT;
sub _md4_perl_generated {
BEGIN { \$^H |= 1; }; # use integer
my (\$A,\$B,\$C,\$D)=(0x67452301,0xefcdab89,0x98badcfe,0x10325476);
my (\$a,\$b,\$c,\$d,\$t,\$i);
my \$dr=shift;
my \$l=length(\$\$dr);
for my \$L (0 .. ((\$l/64)-1) ) {
my \@D = unpack('V16', substr(\$\$dr, \$L*64,64));
(\$a,\$b,\$c,\$d)=(\$A,\$B,\$C,\$D);
EOT
for ( $i = 0 ; $i < 16 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .= "\$t=((\$$d^(\$$b\&(\$$c^\$$d)))+\$$a+\$D[$M[$i]])$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1))))$M;\n";
}
for ( ; $i < 32 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .=
"\$t=(( (\$$b&\$$c)|(\$$b&\$$d)|(\$$c&\$$d) )+\$$a+\$D[$M[$i]]+0x5a827999)$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1))))$M;\n";
}
for ( ; $i < 48 ; $i++ ) {
my ( $a, $b, $c, $d ) =
split( '', substr( $N, ( $i % 4 ) * 4, 4 ) );
$code .=
"\$t=(( \$$b^\$$c^\$$d )+\$$a+\$D[$M[$i]]+0x6ed9eba1)$M;\n";
$code .=
"\$$a=(((\$t<<$S[$i])|((\$t>>(32-$S[$i]))&((1<<$S[$i])-1))))$M;\n";
}
$code .= <<EOT;
\$A=\$A+\$a\&0xffffffff; \$B=\$B+\$b\&0xffffffff;
\$C=\$C+\$c\&0xffffffff; \$D=\$D+\$d\&0xffffffff;
} # for
return unpack('H*', pack('V4',\$A,\$B,\$C,\$D)); }
EOT
eval "$code";
my $TEST = _md5_pad('foobar');
if ( _md4_perl_generated( \$TEST ) ne
'547aefd231dcbaac398625718336f143' )
{
utils_carp('md4: MD4 self-test not successful.');
}
}
}    # md4 package container
sub multipart_set {
my ( $hr, $n, $v ) = @_;
return if ( !ref($hr) );    # error check
return undef if ( !defined $n || $n eq '' );
$$hr{$n} = $v;
}
sub multipart_get {
my ( $hr, $n ) = @_;
return undef if ( !ref($hr) );                 # error check
return undef if ( !defined $n || $n eq '' );
return $$hr{$n};
}
sub multipart_setfile {
my ( $hr, $n, $path ) = ( shift, shift, shift );
my ($fname) = shift;
return undef if ( !ref($hr) );                 # error check
return undef if ( !defined $n || $n eq '' );
return undef if ( !defined $path );
return undef if ( !( -e $path && -f $path ) );
if ( !defined $fname ) {
$path =~ m/[\\\/]([^\\\/]+)$/;
$fname = $1 || "whisker-file";
}
$$hr{$n} = "\0FILE";
$$hr{"\0$n"} = [ $path, $fname ];
return 1;
}
sub multipart_getfile {
my ( $hr, $n ) = @_;
return undef if ( !ref($hr) );                                 # error check
return undef if ( !defined $n || $n eq '' );
return undef if ( !defined $$hr{$n} || $$hr{$n} ne "\0FILE" );
return @{ $$hr{"\0$n"} };
}
sub multipart_boundary {
my ( $hr, $new ) = @_;
my $ret;
return undef if ( !ref($hr) );    # error check
if ( !defined $$hr{"\0BOUNDARY"} ) {
my $b  = uc( utils_randstr(20) );
my $b2 = '-' x 32;
$$hr{"\0BOUNDARY"} = "$b2$b";
}
$ret = $$hr{"\0BOUNDARY"};
if ( defined $new ) {
$$hr{"\0BOUNDARY"} = $new;
}
return $ret;
}
sub multipart_write {
my ( $mp, $hr ) = @_;
return undef if ( !ref($mp) );    # error check
return undef if ( !ref($hr) );    # error check
if ( !defined $$mp{"\0BOUNDARY"} ) {
my $b  = uc( utils_randstr(20) );
my $b2 = '-' x 32;
$$mp{"\0BOUNDARY"} = "$b2$b";
}
my $B   = $$mp{"\0BOUNDARY"};
my $EOL = $$hr{whisker}->{http_eol} || "\x0d\x0a";
my $keycount = 0;
foreach ( keys %$mp ) {
next if ( substr( $_, 0, 1 ) eq "\0" );
$keycount++;
if ( $$mp{$_} eq "\0FILE" ) {
my ( $path, $name ) = multipart_getfile( $mp, $_ );
next if ( !defined $path );
$$hr{whisker}->{data} .= "$B$EOL";
$$hr{whisker}->{data} .=
"Content-Disposition: " . "form-data; name=\"$_\"; ";
$$hr{whisker}->{data} .= "filename=\"$name\"$EOL";
$$hr{whisker}->{data} .=
"Content-Type: " . "application/octet-stream$EOL";
$$hr{whisker}->{data} .= $EOL;
next if ( !open( IN, "<$path" ) );
binmode(IN);    # stupid Windows
while (<IN>) {
$$hr{whisker}->{data} .= $_;
}
close(IN);
$$hr{whisker}->{data} .= $EOL;    # WARNING: is this right?
}
else {
$$hr{whisker}->{data} .= "$B$EOL";
$$hr{whisker}->{data} .=
"Content-Disposition: " . "form-data; name=\"$_\"$EOL";
$$hr{whisker}->{data} .= "$EOL$$mp{$_}$EOL";
}
}
if ($keycount) {
$$hr{whisker}->{data} .= "$B--$EOL";    # closing boundary
$$hr{"Content-Length"} = length( $$hr{whisker}->{data} );
$$hr{"Content-Type"}   = "multipart/form-data; boundary=$B";
return 1;
}
else {
return undef;
}
}
sub multipart_read {
my ( $mp, $hr, $fp ) = @_;
return undef if ( !( defined $mp && ref($mp) ) );
return undef if ( !( defined $hr && ref($hr) ) );
my $ctype = utils_find_lowercase_key( $hr, 'content-type' );
return undef if ( !defined $ctype );
return undef if ( $ctype !~ m#^multipart/form-data#i );
return multipart_read_data( $mp, \$$hr{'whisker'}->{'data'}, undef, $fp );
}
sub multipart_read_data {
my ( $mp, $dr, $bound, $fp ) = @_;
return undef if ( !( defined $mp && ref($mp) ) );
return undef if ( !( defined $dr && ref($dr) ) );
if ( !defined $bound ) {
if ( $$dr =~ /([-]{5,}[A-Z0-9]+)[\r\n]/i ) {
$bound = $1;
}
else {
return undef;
}
}
if ( defined $fp && !( -d $fp && -w $fp ) ) {
$fp = undef;
}
my $line = utils_getline_crlf( $dr, 0 );
return undef if ( !defined $line );
return undef if ( index( $line, $bound ) != 0 );
my $done = 0;
while ( !$done ) {
$done = _multipart_read_data_part( $mp, $dr, $bound, $fp );
}
return 1;
}
sub _multipart_read_data_part {
my ( $mp, $dr, $bound, $fp ) = @_;
my $dispinfo = utils_getline_crlf($dr);
return 1 if ( !defined $dispinfo );
return 1 if ( length($dispinfo) == 0 );
my $lcdisp = lc($dispinfo);
if ( index( $lcdisp, 'content-disposition: form-data;' ) != 0 ) {
return 1;
}    # bad disposition
my ( $s, $e, $l );
$s = index( $lcdisp, 'name="', 30 );
$e = index( $lcdisp, '"',      $s + 6 );
return 1 if ( $s == -1 || $e == -1 );
my $NAME = substr( $dispinfo, $s + 6, $e - $s - 6 );
$s = index( $lcdisp, 'filename="', $e );
my $FILENAME = undef;
if ( $s != -1 ) {
$e = index( $lcdisp, '"', $s + 10 );
return 1 if ( $e == -1 );    # puke; malformed filename
$FILENAME = substr( $dispinfo, $s + 10, $e - $s - 10 );
$s        = rindex( $FILENAME, '\\' );
$e        = rindex( $FILENAME, '/' );
$s = $e if ( $e > $s );
$FILENAME = substr( $FILENAME, $s + 1, length($FILENAME) - $s );
}
my $CTYPE = utils_getline_crlf($dr);
return 1 if ( !defined $CTYPE );
$CTYPE = lc($CTYPE);
if ( length($CTYPE) > 0 ) {
$s = index( $CTYPE, 'content-type:' );
return 1 if ( $s != 0 );    # bad ctype line
$CTYPE = substr( $CTYPE, 13, length($CTYPE) - 13 );
$CTYPE =~ tr/ \t//d;
my $xx = utils_getline_crlf($dr);
return 1 if ( !defined $xx );
return 1 if ( length($xx) > 0 );
}
else {
$CTYPE = 'application/octet-stream';
}
my $VALUE = '';
while ( defined( $l = utils_getline_crlf($dr) ) ) {
last if ( index( $l, $bound ) == 0 );
$VALUE .= $l;
$VALUE .= "\r\n";
}
substr( $VALUE, -2, 2 ) = '';
if ( !defined $FILENAME ) {    # read in param
$$mp{$NAME} = $VALUE;
return 0;
}
else {                         # read in file
$$mp{$NAME} = "\0FILE";
return 0 if ( !defined $fp );
if ( $CTYPE ne 'application/octet-stream' ) {
return 0;
}
my $rfn      = lc( utils_randstr(12) );
my $fullpath = "$fp$rfn";
$$mp{"\0$NAME"} = [ undef, $FILENAME ];
return 0 if ( !open( OUT, ">$fullpath" ) );    # error opening file
binmode(OUT);                                  # stupid Windows
$$mp{"\0$NAME"} = [ $fullpath, $FILENAME ];
print OUT $VALUE;
close(OUT);
return 0;
}    # if !defined $FILENAME
return 0;    # um, this should never be reached...
}
sub multipart_files_list {
my ($mp) = shift;
my @ret;
return () if ( !( defined $mp && ref($mp) ) );
while ( my ( $K, $V ) = each(%$mp) ) {
push( @ret, $K ) if ( $V eq "\0FILE" );
}
return @ret;
}
sub multipart_params_list {
my ($mp) = shift;
my @ret;
return () if ( !( defined $mp && ref($mp) ) );
while ( my ( $K, $V ) = each(%$mp) ) {
push( @ret, $K ) if ( $V ne "\0FILE"
&& substr( $K, 0, 1 ) ne "\0" );
}
return @ret;
}
sub ntlm_new {
my ( $user, $pass, $domain, $flag ) = @_;
$flag ||= 0;
return undef if ( !defined $user );
$pass   ||= '';
$domain ||= '';
my @a = ( "$user", "$pass", "$domain", undef, undef );
my $t;
if ( $flag == 0 ) {
$t = substr( $pass, 0, 14 );
$t =~ tr/a-z/A-Z/;
$t .= "\0" x ( 14 - length($t) );
$a[3] = des_E_P16($t);    # LanMan password hash
$a[3] .= "\0" x ( 21 - length( $a[3] ) );
}
$t = md4( encode_unicode($pass) );
$t =~ s/([a-z0-9]{2})/sprintf("%c",hex($1))/ieg;
$t .= "\0" x ( 21 - length($t) );
$a[4] = $t;                   # NTLM password hash
&des_cache_reset();           # reset the keys hash
return \@a;
}
sub ntlm_generate_responses {
my ( $obj, $chal ) = @_;
return ( undef, undef ) if ( !defined $obj || !defined $chal );
return ( undef, undef ) if ( !ref($obj) );
my $x = '';
$x = des_E_P24( $obj->[3], $chal ) if ( defined $obj->[3] );
return ( $x, des_E_P24( $obj->[4], $chal ) );
}
sub ntlm_decode_challenge {
return undef if ( !defined $_[0] );
my $chal = shift;
my @res;
@res = unpack( 'Z8VvvVVa8a8a8', substr( $chal, 0, 48 ) );
push( @res, substr( $chal, 48 ) );
unshift( @res, substr( $chal, $res[4], $res[2] ) );
return @res;
}
sub ntlm_header {
my ( $s, $h, $o ) = @_;
my $l = length($s);
return pack( 'vvV', 0, 0, $o - $h ) if ( $l == 0 );
return pack( 'vvV', $l, $l, $o );
}
sub ntlm_client {
my ( $obj, $p ) = @_;
my $resp = "NTLMSSP\0";
return undef if ( !defined $obj || !ref($obj) );
if ( defined $p && $p ne '' ) {    # answer challenge
$p =~ tr/ \t\r\n//d;
$p = decode_base64($p);
my @c  = ntlm_decode_challenge($p);
my $uu = encode_unicode( $obj->[0] );    # username
$resp .= pack( 'V', 3 );
my ( $hl, $hn ) = ntlm_generate_responses( $obj, $c[7] );    # token
return undef if ( !defined $hl || !defined $hn );
my $o = 64;
$resp .= ntlm_header( $hl, 64, $o );                         # LM hash
$resp .= ntlm_header( $hn, 64, ( $o += length($hl) ) );      # NTLM hash
$resp .= ntlm_header( $c[0], 64, ( $o += length($hn) ) );    # domain
$resp .= ntlm_header( $uu, 64, ( $o += length( $c[0] ) ) );  # username
$resp .= ntlm_header( $uu, 64, ( $o += length($uu) ) );    # workstation
$resp .= ntlm_header( '', 64, ( $o += length($uu) ) );     # session
$resp .= pack( 'V', $c[6] );
$resp .= $hl . $hn . $c[0] . $uu . $uu;
}
else {    # initiate challenge
$resp .= pack( 'VV', 1, 0x0000b207 );
$resp .= ntlm_header( $obj->[0], 32, 32 );
$resp .= ntlm_header( $obj->[2], 32, 32 + length( $obj->[0] ) );
$resp .= $obj->[0] . $obj->[2];
}
return encode_base64( $resp, '' );
}
sub _ntlm_auth_callback {
my ( $stream, $hi, $ho, $pflag ) = @_;
my ( $ntlmobj, $header, $req_pre, $req_post, $aheader, $work, $ecode );
my ($rheader);
$pflag ||= 0;
if ($pflag) {
$ntlmobj                  = $$hi{whisker}->{auth_proxy_data};
$header                   = 'Proxy-Authorization';
$rheader                  = 'proxy-authenticate';
$ecode                    = 407;
$hi->{'Proxy-Connection'} = 'Keep-Alive';
}
else {
$ntlmobj          = $$hi{whisker}->{auth_data};
$header           = 'Authorization';
$rheader          = 'www-authenticate';
$ecode            = 401;
$hi->{Connection} = 'Keep-Alive';
}
$ho->{whisker}->{error} = 'NTLM ' . $header;
$hi->{$header} = 'NTLM ' . ntlm_client($ntlmobj);
my $ret = _http_do_request_ex( $stream, $hi, $ho );
return $ret if ($ret);
return 200  if ( $$ho{whisker}->{code} == 200 );
return 1    if ( $$ho{whisker}->{code} != $ecode );
my $thead = utils_find_lowercase_key( $ho, $rheader );
return 1 if ( !defined $thead );
my ( $found, @auths );
if ( ref($thead) ) { @auths = @$thead; }
else { push @auths, $thead; }
foreach (@auths) {
$found = $1 if (m/^NTLM (.+)$/);
}
return 1 if ( !defined $found );
$hi->{$header} = 'NTLM ' . ntlm_client( $ntlmobj, $found );
push @{ $hi->{whisker}->{header_delete_on_success} }, $header;
return 0;
}
sub _ntlm_auth_proxy_callback {
return _ntlm_auth_callback( $_[0], $_[1], $_[2], 1 );
}
{    # start of DES local container #######################################
my $generated = 0;
my $perm1     = [
57, 49, 41, 33, 25, 17, 9,  1,  58, 50, 42, 34, 26, 18,
10, 2,  59, 51, 43, 35, 27, 19, 11, 3,  60, 52, 44, 36,
63, 55, 47, 39, 31, 23, 15, 7,  62, 54, 46, 38, 30, 22,
14, 6,  61, 53, 45, 37, 29, 21, 13, 5,  28, 20, 12, 4
];
my $perm2 = [
14, 17, 11, 24, 1,  5,  3,  28, 15, 6,  21, 10, 23, 19, 12, 4,
26, 8,  16, 7,  27, 20, 13, 2,  41, 52, 31, 37, 47, 55, 30, 40,
51, 45, 33, 48, 44, 49, 39, 56, 34, 53, 46, 42, 50, 36, 29, 32
];
my $perm3 = [
58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4,
62, 54, 46, 38, 30, 22, 14, 6, 64, 56, 48, 40, 32, 24, 16, 8,
57, 49, 41, 33, 25, 17, 9,  1, 59, 51, 43, 35, 27, 19, 11, 3,
61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7
];
my $perm4 = [
32, 1,  2,  3,  4,  5,  4,  5,  6,  7,  8,  9,  8,  9,  10, 11,
12, 13, 12, 13, 14, 15, 16, 17, 16, 17, 18, 19, 20, 21, 20, 21,
22, 23, 24, 25, 24, 25, 26, 27, 28, 29, 28, 29, 30, 31, 32, 1
];
my $perm5 = [
16, 7, 20, 21, 29, 12, 28, 17, 1,  15, 23, 26, 5,  18, 31, 10,
2,  8, 24, 14, 32, 27, 3,  9,  19, 13, 30, 6,  22, 11, 4,  25
];
my $perm6 = [
40, 8, 48, 16, 56, 24, 64, 32, 39, 7, 47, 15, 55, 23, 63, 31,
38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29,
36, 4, 44, 12, 52, 20, 60, 28, 35, 3, 43, 11, 51, 19, 59, 27,
34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9,  49, 17, 57, 25
];
my $sc = [ 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1 ];
sub des_E_P16 {
my ($p14) = @_;
my $sp8 = [ 0x4b, 0x47, 0x53, 0x21, 0x40, 0x23, 0x24, 0x25 ];
my $p7 = substr( $p14, 0, 7 );
my $p16 = des_smbhash( $sp8, $p7 );
$p7 = substr( $p14, 7, 7 );
$p16 .= des_smbhash( $sp8, $p7 );
return $p16;
}
sub des_E_P24 {
my ( $p21, $c8_str ) = @_;
my @c8 = map { ord($_) } split( //, $c8_str );
my $p24 = des_smbhash( \@c8, substr( $p21, 0, 7 ) );
$p24 .= des_smbhash( \@c8, substr( $p21, 7,  7 ) );
$p24 .= des_smbhash( \@c8, substr( $p21, 14, 7 ) );
}
sub des_permute {
my ( $i, $out, $in, $p, $n ) = ( 0, @_ );
foreach $i ( 0 .. ( $n - 1 ) ) {
$out->[$i] = $in->[ $p->[$i] - 1 ];
}
}
sub des_lshift {
my ( $c, $d, $count ) = @_;
my ( @outc, @outd, $i, $x );
while ( $count-- ) {
push @$c, shift @$c;
push @$d, shift @$d;
}
}
my %dohash_cache;    # cache for key data; saves some cycles
my %key_cache;       # another cache for key data
sub des_cache_reset {
%dohash_cache = ();
%key_cache    = ();
}
sub des_dohash {
my ( $out, $in, $key ) = @_;
my ( $i, $j, $k, @pk1, @c, @d, @cd, @ki, @pd1, @l, @r, @rl );
&des_permute( \@pk1, $key, $perm1, 56 );
for ( $i = 0 ; $i < 28 ; $i++ ) {
$c[$i] = $pk1[$i];
$d[$i] = $pk1[ $i + 28 ];
}
for ( $i = 0 ; $i < 16 ; $i++ ) {
my @array;
&des_lshift( \@c, \@d, $sc->[$i] );
@cd = ( @c, @d );
&des_permute( \@array, \@cd, $perm2, 48 );
$ki[$i] = \@array;
}
des_dohash2( $in, \@l, \@r, \@ki );
@rl = ( @r, @l );
&des_permute( $out, \@rl, $perm6, 64 );
}
sub des_str_to_key {
my ($str) = @_;
my ( $i, @key, $out, @str );
unshift( @str, ord($_) ) while ( $_ = chop($str) );
$key[0] = $str[0] >> 1;
$key[1] = ( ( $str[0] & 0x01 ) << 6 ) | ( $str[1] >> 2 );
$key[2] = ( ( $str[1] & 0x03 ) << 5 ) | ( $str[2] >> 3 );
$key[3] = ( ( $str[2] & 0x07 ) << 4 ) | ( $str[3] >> 4 );
$key[4] = ( ( $str[3] & 0x0f ) << 3 ) | ( $str[4] >> 5 );
$key[5] = ( ( $str[4] & 0x1f ) << 2 ) | ( $str[5] >> 6 );
$key[6] = ( ( $str[5] & 0x3f ) << 1 ) | ( $str[6] >> 7 );
$key[7] = $str[6] & 0x7f;
foreach $i ( 0 .. 7 ) {
$key[$i] = 0xff & ( $key[$i] << 1 );
}
@{ $key_cache{$str} } = @key;
return \@key;
}
sub des_smbhash {
my ( $in, $key ) = @_;
my $key2;
&des_generate if ( !$generated );
if ( defined $key_cache{$key} ) {
$key2 = $key_cache{$key};
}
else { $key2 = &des_str_to_key($key); }
my ( $i, $div, $mod, @in, @outb, @inb, @keyb, @out );
foreach $i ( 0 .. 63 ) {
$div = int( $i / 8 );
$mod = $i % 8;
$inb[$i]  = ( $in->[$div] &   ( 1 << ( 7 - ($mod) ) ) ) ? 1 : 0;
$keyb[$i] = ( $key2->[$div] & ( 1 << ( 7 - ($mod) ) ) ) ? 1 : 0;
$outb[$i] = 0;
}
&des_dohash( \@outb, \@inb, \@keyb );
foreach $i ( 0 .. 7 ) { $out[$i] = 0; }
foreach $i ( 0 .. 63 ) {
$out[ int( $i / 8 ) ] |= ( 1 << ( 7 - ( $i % 8 ) ) )
if ( $outb[$i] );
}
my $out = pack( "C8", @out );
return $out;
}
sub des_generate {    # really scary dragons here....this code is optimized
my ( $i, $j );
my $code = <<EOT;
{ my \$sbox = [[
[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],[0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8],
[4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]
],[
[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],[3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
[0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],[13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]
],[
[10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8],[13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1],
[13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7],[1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12]
],[
[7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15],[13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9],
[10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4],[3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14]
],[
[2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9],[14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6],
[4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14],[11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3]
],[
[12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11],[10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8],
[9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6],[4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13]
],[
[4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1],[13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6],
[1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2],[6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12]
],[
[13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7],[1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2],
[7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8],[2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11]
]];
EOT
$code .=
'sub des_dohash2 { my ($in,$l,$r,$ki)=@_; my (@p,$i,$j,$k,$m,$n);';
for ( $i = 0 ; $i < 64 ; $i++ ) {
$code .= "\$p[$i] = \$in->[" . ( $perm3->[$i] - 1 ) . "];\n";
}
for ( $i = 0 ; $i < 32 ; $i++ ) {
$code .= "\$l->[$i]=\$p[$i]; \$r->[$i]=\$p[" . ( $i + 32 ) . "];\n";
}
$code .= 'for($i=0;$i<16;$i++){ local (@er,@erk,@b,@cb,@pcb,@r2);';
for ( $i = 0 ; $i < 48 ; $i++ ) {
$code .=
"\$erk[$i]=\$r->["
. ( $perm4->[$i] - 1 )
. "]^(\$ki->[\$i]->[$i]);\n";
}
for ( $i = 0 ; $i < 8 ; $i++ ) {
for ( $j = 0 ; $j < 6 ; $j++ ) {
$code .= "\$b[$i][$j]=\$erk[" . ( $i * 6 + $j ) . "];\n";
}
}
for ( $i = 0 ; $i < 8 ; $i++ ) {
$code .= "\$m=(\$b[$i][0]<<1)|\$b[$i][5];\n";
$code .=
"\$n=(\$b[$i][1]<<3)|(\$b[$i][2]<<2)|(\$b[$i][3]<<1)|\$b[$i][4];\n";
for ( $j = 0 ; $j < 4 ; $j++ ) {
$code .=
"\$b[$i][$j]=(\$sbox->[$i][\$m][\$n]&"
. ( 1 << ( 3 - $j ) )
. ")?1:0;\n";
}
}
for ( $i = 0 ; $i < 8 ; $i++ ) {
for ( $j = 0 ; $j < 4 ; $j++ ) {
$code .= "\$cb[" . ( $i * 4 + $j ) . "]=\$b[$i][$j];\n";
}
}
for ( $i = 0 ; $i < 32 ; $i++ ) {
$code .= "\$pcb[$i]=\$cb[" . ( $perm5->[$i] - 1 ) . "];\n";
}
for ( $i = 0 ; $i < 32 ; $i++ ) {
$code .= "\$r2[$i]=(\$l->[$i])^\$pcb[$i];\n";
}
for ( $i = 0 ; $i < 32 ; $i++ ) {
$code .= "\$l->[$i]=\$r->[$i]; \$r->[$i]=\$r2[$i];\n";
}
$code .= '}}}';
eval "$code";
print "DEBUG: $code\n\n";
$generated++;
}
}    ##### end of DES container ################################################
sub get_page {
my ( $URL, $hr ) = ( shift, shift );
return ( undef, 'No URL supplied' ) if ( length($URL) == 0 );
my ( %req, %resp );
my $rptr;
if ( defined $hr && ref($hr) ) {
$rptr = $hr;
}
else {
$rptr = \%req;
http_init_request( \%req );
}
my @u = uri_split( $URL, $rptr );
return ( undef, 'Non-HTTP URL supplied' )
if ( $u[1] ne 'http' && $u[1] ne 'https' );
http_fixup_request($rptr);
if ( http_do_request( $rptr, \%resp ) ) {
return ( undef, $resp{'whisker'}->{'error'} );
}
return ( $resp{'whisker'}->{'code'}, $resp{'whisker'}->{'data'} );
}
sub get_page_hash {
my ( $URL, $hr ) = ( shift, shift );
return undef if ( length($URL) == 0 );
my ( %req, %resp );
my $rptr;
if ( defined $hr && ref($hr) ) {
$rptr = $hr;
}
else {
$rptr = \%req;
http_init_request( \%req );
}
my @u = uri_split( $URL, $rptr );    # this is newer >=1.1 syntax
return undef if ( $u[1] ne 'http' && $u[1] ne 'https' );
http_fixup_request($rptr);
my $r = http_do_request( $rptr, \%resp );
$resp{whisker}->{get_page_hash} = $r;
return \%resp;
}
sub get_page_to_file {
my ( $URL, $filepath, $hr ) = @_;
return undef if ( length($URL) == 0 );
return undef if ( length($filepath) == 0 );
my ( %req, %resp );
my $rptr;
if ( defined $hr && ref($hr) ) {
$rptr = $hr;
}
else {
$rptr = \%req;
http_init_request( \%req );
}
my @u = uri_split( $URL, $rptr );    # this is newer >=1.1 syntax
return undef if ( $u[1] ne 'http' && $u[1] ne 'https' );
http_fixup_request($rptr);
return undef if ( http_do_request( $rptr, \%resp ) );
open( OUT, ">$filepath" ) || return undef;
binmode(OUT);                        # stupid Windows
print OUT $resp{'whisker'}->{'data'};
close(OUT);
return $resp{'whisker'}->{'code'};
}
@_stream_FUNCS = (
[ 'open', 'close', 'read', 'write', 'writedone', 'valid' ],    # stream_NULL
[ 'socket', 'all', 'socket', 'socket', 'noop', 'socket' ]
,    # stream_SOCKTCP   1
[ 'socket', 'all', 'socket', 'socket', 'noop', 'never' ]
,    # stream_SOCKUDP   2
[ 'file', 'all', 'socket', 'file', 'noop', 'never' ],   # stream_FILE      3
[ 'ssl', 'all', 'ssl', 'ssl', 'noop', 'netssleay' ],    # stream_NETSSLEAY 4
[ 'ssl', 'all', 'ssl', 'ssl', 'noop', 'never' ],        # stream_NETSSL    5
[ 'buffer', 'buffer', 'buffer', 'buffer', 'noop',
'never' ]                                           # stream_BUFFER    6
);
sub stream_key {
my ( $key, $type, $wh ) = ( '', 1, shift );
if ( defined $wh->{whisker}->{UDP} && $wh->{whisker}->{UDP} > 0 ) {
$type = 2;
$key  = 'udp:';
}
if ( $wh->{whisker}->{ssl} > 0 ) {
$type = 4 if ( $LW_SSL_LIB == 1 );
$type = 5 if ( $LW_SSL_LIB == 2 );
$key = 'ssl:';
}
if ( defined $wh->{whisker}->{file_stream} ) {
$type = 3;
$key  = 'file=' . $wh->{whisker}->{file_stream} . ':';
}
if ( defined $wh->{whisker}->{buffer_stream} ) {
$type = 6;
$key  = 'buffer:';
}
my ( $x, $h, $p ) = (0);
if ( defined $wh->{whisker}->{proxy_host} ) {
$h = $wh->{whisker}->{proxy_host};
$p = $wh->{whisker}->{proxy_port} || 80;
$x++;
$key .= 'proxy:';
if ( $type == 5 ) {
$x                = 0;
$ENV{HTTPS_PROXY} = "$h:$p";
$h                = $wh->{whisker}->{host};
$p                = $wh->{whisker}->{port};
}
}
else {
$h = $wh->{whisker}->{host};
$p = $wh->{whisker}->{port};
}
$key .= $h . ':' . $p;
if ( defined $wh->{whisker}->{stream_num} ) {
$key .= '/' . $wh->{whisker}->{stream_num};
}
return $key if ( !wantarray() );
return ( $type, $h, $p, $x, $key );
}
sub stream_setsock {
my $fd = shift;
my $wh = http_new_request( host => 'localhost', port => 80, ssl => 0 );
my $xr = stream_new($wh);
return undef if ( $xr->{streamtype} != 1 );
$xr->{sock}  = $fd;
$xr->{state} = 1;
$xr->{eof}   = 0;
$xr->{clearall}->();
return $xr;
}
{
$SYMCOUNT = 0;
sub stream_new {
my ( $c, $rh ) = ( 0, shift );
my $sock = _stream_newsock();
my %x;
%x = (
bufin      => '',
bufout     => '',
error      => '',
streamtype => 0,
eof        => 0,
ctx        => undef,
sock       => $sock,
state      => 0,
syns       => 0,
reqs       => 0,
timeout    => $rh->{whisker}->{timeout} || 10,
nonblock   => 0,
forceclose => 0
);
( $x{streamtype}, $x{chost}, $x{cport}, $x{proxy}, $x{key} ) =
stream_key($rh);
return undef if ( $x{streamtype} == 0 );
return undef
if (
$LW_SSL_LIB == 0
&& (   $x{streamtype} == 4
|| $x{streamtype} == 5 )
);
return undef
if ( $x{streamtype} != 3
&& $x{streamtype} != 6
&& !defined $Socket::VERSION );
$x{nonblock} = $LW_NONBLOCK_CONNECT if ( $x{streamtype} == 1 );
$x{forceclose} = 1 if ( $x{streamtype} == 5 );
$x{slurp} = $rh->{whisker}->{trailing_slurp} || 0;
my @N = @{ $_stream_FUNCS[ $x{streamtype} ] };
for ( $c = 0 ; $c < 6 ; $c++ ) {
my $n = $_stream_FUNCS[0]->[$c];
my $e =
'$x{"' . $n . '"}=sub{&_stream_' . $N[$c] . "_$n" . '(\%x,@_)}';
eval "$e";
}
$x{queue} = sub { $x{bufout} .= shift };
$x{clearall} = sub { $x{bufin} = $x{bufout} = '' };
$x{clear} = sub { $x{bufout} = '' };
return bless \%x, 'LW2::stream';
}
sub _stream_newsock {    # same as Symbol::gensym
my $pkg  = "LW2::";
my $name = "_STREAM_" . $SYMCOUNT++;
delete $$pkg{$name};
return \*{ $pkg . $name };
}
}
sub _stream_all_close {
my $xr = shift;
$xr->{state} = 0;
if ( $xr->{streamtype} == 4 ) {
eval { $xr->{sock}->shutdown() };
eval { close( $xr->{origsock} ) };
}
else {
eval { close( $xr->{sock} ) };
}
}
sub _stream_never_valid {
return 0;
}
sub __bad_netssleay_error {
my $err = Net::SSLeay::ERR_get_error;
return 0
if ( $err == Net::SSLeay::ERROR_NONE
|| $err == Net::SSLeay::ERROR_WANT_READ
|| $err == Net::SSLeay::ERROR_WANT_WRITE );
return 1;
}
sub _stream_netssleay_valid {
my $xr = shift;
return 0 if ( $LW_SSL_KEEPALIVE == 0 || $xr->{state} == 0 );
return 0 if ( &Net::SSLeay::OPENSSL_VERSION_NUMBER < 0x0090601f );
my $lo = Net::SSLeay::pending( $xr->{sock} );
if ( $lo > 0 ) {    # leftover data to slurp
if ( !$xr->{slurp} ) {
return 0 if ( !_stream_ssl_read($xr) );
}
else {
}
}
return 0 if ( __bad_netssleay_error() );
my ( $r, $e, $vin ) = ( undef, undef, '' );
my $fno = fileno( $xr->{origsock} );
vec( $vin, $fno, 1 ) = 1;
if ( select( ( $r = $vin ), undef, ( $e = $vin ), .0001 ) ) {
return 0 if ( vec( $e, $fno, 1 ) );
if ( vec( $r, $fno, 1 ) ) {    # waiting data, let's peek
my $temp = Net::SSLeay::peek( $xr->{sock}, 1 );
return 0 if ( __bad_netssleay_error() );
return 0 if ( $temp <= 0 );
}
}
return 1;
}
sub _stream_socket_valid {
my $xr = shift;
return 0 if ( $xr->{state} == 0 );
my ( $o, $vin ) = ( undef, '' );
vec( $vin, fileno( $xr->{sock} ), 1 ) = 1;
if ( select( ( $o = $vin ), undef, undef, .0001 ) ) {
my ( $hold, $res );
do {
$res = sysread( $xr->{sock}, $hold, 4096 );
return _stream_err( $xr, 1, 'is_valid sysread failed' )
if ( !defined $res );    # error
return 0 if ( $res == 0 ); # EOF
if ( !$xr->{slurp} ) {
$xr->{bufin} .= $hold;
}
else {
$xr->{slurped} .= $hold . "\0";
}
} while ( $res && select( ( $o = $vin ), undef, undef, .0001 ) );
}
return 1;
}
sub _stream_socket_read {
my $xr = shift;
return 0 if ( $xr->{state} == 0 );
my ( $vin, $t ) = ( '', '' );
vec( $vin, fileno( $xr->{sock} ), 1 ) = 1;
return 0 if ( !select( $vin, undef, undef, $xr->{timeout} ) );
my $res = sysread( $xr->{sock}, $t, 4096 );
return _stream_err( $xr, 1, 'sysread failed' ) if ( !defined $res );
if ( $res == 0 ) {
$xr->{eof} = 1;
return 0;
}
$xr->{bufin} .= $t;
$xr->{eof} = 0;
return 1;
}
sub _stream_ssl_read {
my ( $xr, $t ) = ( shift, '' );
return 0 if ( $xr->{state} == 0 );
if ( $xr->{streamtype} == 4 ) {
local $SIG{ALRM} = sub { die "lw_timeout\n" };
local $SIG{PIPE} = sub { die "lw_pipe\n" };
eval {
eval { alarm( $xr->{timeout} ) };
$t = Net::SSLeay::read( $xr->{sock} );
eval { alarm(0) };
};
return 0 if ( $@ || __bad_netssleay_error() || !defined $t || $t eq '' );
}
elsif ( $xr->{streamtype} == 5 ) {
return 0 if ( !$xr->{sock}->read( $t, 4096 ) );
}
$xr->{bufin} .= $t;
return 1;
}
sub _stream_noop_writedone { }
sub _stream_ssl_writedone {
my $xr = shift;
if ( $xr->{streamtype} == 4 ) {    # Net::SSLeay
shutdown $xr->{origsock}, 1;
}
else {                             # Net::SSL
}
}
sub _stream_socket_write {
my ( $xr, $data, $v, $wrote ) = ( shift, shift, '', 0 );
return 0 if ( $xr->{state} == 0 );
$xr->{bufout} .= $data if ( defined $data );
my $len = length( $xr->{bufout} );
return 1 if ( $len == 0 );
vec( $v, fileno( $xr->{sock} ), 1 ) = 1;
return _stream_err( $xr, 1, 'stream write test failed' )
if ( !select( undef, $v, undef, .0001 ) );
my $piperr = 0;
local $SIG{PIPE} = sub { $piperr++ };
do {
$wrote = syswrite( $xr->{sock}, $xr->{bufout}, $len );
if ( defined $wrote ) {
substr( $xr->{bufout}, 0, $wrote ) = '';
}
else {
if ( $! != EWOULDBLOCK ) {
$piperr++;
}
else {
vec( $v, fileno( $xr->{sock} ), 1 ) = 1;
$piperr++ if ( !select( undef, $v, undef, $xr->{timeout} ) );
}
}
return _stream_err( $xr, 1, 'syswrite failed' ) if ($piperr);
$len = length( $xr->{bufout} );
} while ( $len > 0 );
return 1;
}
sub _stream_ssl_write {
my ( $xr, $data, $wrote, $err ) = ( shift, shift, 0, '' );
return 0 if ( $xr->{state} == 0 );
$xr->{bufout} .= $data if ( defined $data );
my $len = length( $xr->{bufout} );
return 1 if ( $len == 0 );
if ( $xr->{streamtype} == 4 ) {
( $wrote, $err ) =
Net::SSLeay::ssl_write_all( $xr->{sock}, \$xr->{bufout} );
if ( __bad_netssleay_error() || !$wrote ) {
$xr->{error} = "SSL error: $err";
return 0;
}
if ( $wrote != $len ) {
$xr->{error} = 'could not send entire queue';
return 0;
}
}
elsif ( $xr->{streamtype} == 5 ) {
$xr->{sock}->print( $xr->{bufout} );
}
$xr->{bufout} = '';
return 1;
}
sub _stream_socket_alloc {
my ( $xr, $wh ) = @_;
if ( $xr->{streamtype} == 2 ) {
return _stream_err( $xr, 0, 'socket problems (UDP)' )
if (
!socket(
$xr->{sock}, PF_INET,
SOCK_DGRAM, getprotobyname('udp') || 0
)
);
}
else {
return _stream_err( $xr, 0, 'socket() problems' )
if (
!socket(
$xr->{sock}, PF_INET,
SOCK_STREAM, getprotobyname('tcp') || 0
)
);
}
if ( defined $wh->{whisker}->{bind_socket} ) {
my $p = $wh->{whisker}->{bind_port} || '*';
$p =~ tr/0-9*//cd;
return _stream_err( $xr, 0, 'Bad bind_port value' )
if ( $p eq '' );
my $a = INADDR_ANY;
$a = inet_aton( $wh->{whisker}->{bind_addr} )
if ( defined $wh->{whisker}->{bind_addr} );
return _stream_err( $xr, 0, 'Bad bind_addr value' )
if ( !defined $a );
if ( $p =~ tr/*// ) {
for ( $p = 14011 ; $p < 65535 ; $p++ ) {
if ( !bind( $xr->{sock}, sockaddr_in( $p, $a ) ) ) {
return _stream_err( $xr, 0, 'bind() on socket failed' )
if ( $! ne 'Address already in use' );
}
else {
last;
}
}
return _stream_err( $xr, 0, 'bind() cannot find open socket' )
if ( $p >= 65535 );
}
else {
return _stream_err( $xr, 0, 'bind() on socket failed' )
if ( !bind( $xr->{sock}, sockaddr_in( $p, $a ) ) );
}
}
if ( !defined $xr->{iaton} ) {
$xr->{iaton} = inet_aton( $xr->{chost} );
return _stream_err( $xr, 0, 'can\'t resolve hostname' )
if ( !defined $xr->{iaton} );
}
$xr->{socket_alloc}++;
return 1;
}
sub _stream_socket_nonblock {
my ( $fl, $xr, $nonblock ) = ( 0, @_ );
if ( $^O =~ /Win32/ ) {
$fl = 1 if ($nonblock);
if ( !ioctl( $xr->{sock}, 0x8004667e, \$fl ) ) {
return 0;
}
}
else {
if ( !( $fl = fcntl( $xr->{sock}, F_GETFL, 0 ) ) ) {
return 0;
}
$fl |= O_NONBLOCK if ($nonblock);
$fl &= ~O_NONBLOCK if ( !$nonblock );
if ( !( fcntl( $xr->{sock}, F_SETFL, $fl ) ) ) {
return 0;
}
}
return 1;
}
sub _stream_socket_open {
my ( $vin, $xr, $wh ) = ( '', @_ );
return 0 if ( !defined $wh );
$xr->{'close'}->() if ( $xr->{state} > 0 );
return 0 if ( !_stream_socket_alloc( $xr, $wh ) );
$xr->{timeout} = $wh->{whisker}->{timeout} || 10;
if ( $xr->{nonblock} ) {
if ( !_stream_socket_nonblock( $xr, 1 ) ) {
$xr->{nonblock} = 0;
$LW_NONBLOCK_CONNECT = 0;
}
else {
my $R =
connect( $xr->{sock}, sockaddr_in( $xr->{cport}, $xr->{iaton} ) );
if ( !$R ) {
return _stream_err( $xr, 1, 'can\'t connect (connect error)' )
if ( $! != EINPROGRESS && $! != EWOULDBLOCK );
vec( $vin, fileno( $xr->{sock} ), 1 ) = 1;
return _stream_err( $xr, 1, 'can\'t connect (timeout)' )
if ( !select( undef, $vin, $vin, $xr->{timeout} )
|| !getpeername( $xr->{sock} ) );
}
}
}
if ( !$xr->{nonblock} ) {
eval {
local $SIG{ALRM} = sub { die "timeout\n" };
eval { alarm( $xr->{timeout} ) };
if (
!connect(
$xr->{sock}, sockaddr_in( $xr->{cport}, $xr->{iaton} )
)
)
{
eval { alarm(0) };
die "connect failed\n";
}
eval { alarm(0) };
};
return _stream_err( $xr, 0,
'can\'t connect (' . substr( $@, 0, index( $@, "\n" ) ) . ')' )
if ($@);
}
binmode( $xr->{sock} );
my $S = select( $xr->{sock} );
$|++;
select($S);
$xr->{state} = 1;
$xr->{syns}++;
return 1;
}
sub _stream_ssl_open {
my ( $xr, $wh ) = @_;
return 0         if ( !defined $wh );
$xr->{close}->() if ( $xr->{state} > 0 );
my $W = $wh->{whisker};
if ( $xr->{streamtype} == 5 ) {
$ENV{HTTPS_KEY_FILE}  = $W->{ssl_rsacertfile} || '';
$ENV{HTTPS_CERT_FILE} = $W->{ssl_certfile}    || '';
eval {
$xr->{sock}           = Net::SSL->new(
PeerAddr => $xr->{chost},
PeerPort => $xr->{cport},
Timeout  => $xr->{timeout}
);
};
return _stream_err( $xr, 0, 'can\'t connect: ' . $@ ) 
if ($@ || !defined $xr->{sock});
$xr->{sock}->autoflush(1);
$xr->{state} = 1;
$xr->{syns}++;
return 1;
}
return 0 if ( $xr->{streamtype} != 4 );
if ( !defined $xr->{ctx} ) {
return _stream_err( $xr, 0, 'ssl ctx create' )
if ( !( $xr->{ctx} = Net::SSLeay::CTX_new() ) );
Net::SSLeay::CTX_set_options( $xr->{ctx}, &Net::SSLeay::OP_ALL );
if ( defined $W->{ssl_rsacertfile} ) {
if (
!(
Net::SSLeay::CTX_use_RSAPrivateKey_file(
$xr->{ctx}, $W->{ssl_rsacertfile},
&Net::SSLeay::FILETYPE_PEM
)
)
)
{
return _stream_err( $xr, 0, 'ssl ctx rsacert' );
}
}
if ( defined $W->{ssl_certfile} ) {
if (
!(
Net::SSLeay::CTX_use_certificate_file(
$xr->{ctx}, $W->{ssl_certfile},
&Net::SSLeay::FILETYPE_PEM
)
)
)
{
return _stream_err( $xr, 0, 'ssl ctx cert' );
}
}
}
return _stream_err($xr, 0, 'ssl setup error' )
if( __bad_netssleay_error() );
return _stream_err( $xr, 0, 'ssl create new' )
if ( !( $xr->{sslobj} = Net::SSLeay::new( $xr->{ctx} ) ) );
if ( defined $W->{ssl_ciphers} ) {
if (
!(
Net::SSLeay::set_cipher_list(
$xr->{sslobj}, $W->{ssl_ciphers}
)
)
)
{
return _stream_err( $xr, 0, 'ssl set ciphers' );
}
}
return 0 if ( !_stream_socket_open( $xr, $wh ) );
$xr->{state} = 1;
if ( $xr->{proxy} ) {
my $C = 'CONNECT ' . $W->{host} . ':' . $W->{port} . " HTTP/1.0\r\n";
$C .= 'Proxy-Authorization: ' . $wh->{'Proxy-Authorization'} . "\r\n"
if ( defined $wh->{'Proxy-Authorization'} );
$C .= "\r\n";
my $r = syswrite( $xr->{sock}, $C, length($C) );
return _stream_err( $xr, 1, 'sending proxy connect string' )
if ( !defined $r || $r != length($C) );
do {
return _stream_err( $xr, 1, 'ssl proxy request failed' )
if ( !_stream_socket_read($xr) );
} while ( index( $xr->{bufin}, "\n\n" ) == -1
&& index( $xr->{bufin}, "\r\n\r\n" ) == -1 );
return _stream_err( $xr, 1, 'proxy couldn\'t make connection' )
if ( $xr->{bufin} !~ /^HTTP\/1.[0-9]+\W+200/ );
$xr->{clearall}->();
}
Net::SSLeay::set_fd( $xr->{sslobj}, fileno( $xr->{sock} ) );
Net::SSLeay::set_session( $xr->{sslobj}, $xr->{sslsession} )
if ( defined $xr->{sslsession} );
return _stream_err( $xr, 1, 'ssl connect failed' )
if ( !( Net::SSLeay::connect( $xr->{sslobj} ) ) ||
__bad_netssleay_error() );
$xr->{sslsession} = Net::SSLeay::get_session( $xr->{sslobj} )
if ( defined $W->{ssl_resume} && $W->{ssl_resume} > 0 );
$xr->{origsock} = $xr->{sock};
$xr->{sock}     = $xr->{sslobj};
return 1;
}
sub _stream_file_open {
my ( $xr, $wh ) = @_;
$xr->{close}->() if ( $xr->{state} > 0 );
my $file = $wh->{whisker}->{file_stream};
return _stream_err( $xr, 0, 'invalid file' )
if ( !-e $file || !-f $file );
return _stream_err( $xr, 0, 'file open failure' )
if ( !sysopen( $xr->{sock}, $file, 'r' ) );
binmode($xr->{sock}); # Stupid Windows
$xr->{state} = 1;
}
sub _stream_file_write {
my $xr = shift;
$xr->{bufout} = '';
return 1;
}
sub _stream_buffer_open {
my ( $xr, $wh ) = @_;
$xr->{close}->() if ( $xr->{state} > 0 );
$xr->{state} = 1;
}
sub _stream_buffer_close {
my $xr = shift;
$xr->{state} = 0;
$xr->{bufout} = $xr->{bufin} = '';
}
sub _stream_buffer_read {
my $xr = shift;
return 0 if ( $xr->{state} == 0 );
if ( length( $xr->{bufout} ) > 0 ) {
$xr->{bufin} .= $xr->{bufout};
$xr->{bufout} = '';
}
if ( length( $xr->{bufin} ) == 0 ) {
$xr->{eof} = 1;
return 0;
}
$xr->{eof} = 0;
return 1;
}
sub _stream_buffer_write {
my ( $xr, $data ) = ( shift, shift );
return 0 if ( $xr->{state} == 0 );
$xr->{bufout} .= $data if ( defined $data );
my $len = length( $xr->{bufout} );
return 1 if ( $len == 0 );
$xr->{bufin} .= $xr->{bufout};
$xr->{bufout} = '';
return 1;
}
sub _stream_err {
my ( $xr, $close, $error ) = @_;
$xr->{error} = $error;
$xr->{error} .= ": $!" if ( defined $! && $! ne '' );
$xr->{'close'}->() if ($close);
$xr->{state} = 0;
return 0;
}
sub time_mktime {
my ($sec,$min,$hour,$day,$mon,$yr)=@_;
my @md=(0,31,59,90,120,151,181,212,243,273,304,334);
foreach(@_[0..5]){
return -1 if !defined $_ || $_<0; }
return -1 if($sec>60 || $min>59 || $hour>23 || $day>31 || $mon>11
|| $yr>137 || $yr<70);
$yr += 1900;
my $res = ($yr-1970)*365+$md[$mon];
$res += int(($yr-1969)/4) + int(($yr-1601)/400);
$res -= int(($yr-1901)/100);
$res = ($res+$day-1)*24;
$res = ($res+$hour)*60;
$res = ($res+$min)*60;
return $res+$sec;
}
sub time_gmtolocal {
my $t = shift;
my $now = time;
my $utc = time_mktime(gmtime($now));
my $me = time_mktime(localtime($now));
return $t - ($utc - $me);
}
sub uri_split {
my ( $uri, $work ) = ( shift, '', 0 );
my ($hr) = shift;
my @res = ( undef, undef, undef, 0, undef, undef, undef, undef );
return undef if ( !defined $uri );
( $uri, $res[5] ) = split( '#', $uri, 2 ) if ( index( $uri, '#', 0 ) >= 0 );
my $net_loc = undef;
if ( $uri =~ s/^([-+.a-z0-9A-Z]+):// ) {
$res[1] = lc($1);
if ( substr( $uri, 0, 2 ) eq '//' ) {
my $w = index( $uri, '/', 2 );
if ( $w >= 0 ) {
$net_loc = substr( $uri, 2, $w - 2 );
$uri = substr( $uri, $w, length($uri) - $w );
}
else {
( $net_loc = $uri ) =~ tr#/##d;
$uri = '/';
}
}
}
if ( defined $net_loc ) {
if ( index( $net_loc, '@', 0 ) >= 0 ) {
( $res[6], $net_loc ) = split( /\@/, $net_loc, 2 );
if ( index( $res[6], ':', 0 ) >= 0 ) {
( $res[6], $res[7] ) = split( ':', $res[6], 2 );
}
}
$res[3] = $1 if ( $net_loc =~ s/:([0-9]+)$// );
$res[2] = $net_loc;
}
( $uri, $res[4] ) = split( '\?', $uri, 2 )
if ( index( $uri, '?', 0 ) >= 0 );
$res[0] = $uri;
if ( $res[3] == 0 && defined $res[1] ) {
$res[3] = 80  if ( $res[1] eq 'http' );
$res[3] = 443 if ( $res[1] eq 'https' );
}
my $rel_uri = 0;
$rel_uri++
if ( $res[3] == 0
&& !defined $res[2]
&& !defined $res[1]
&& $res[0] ne '' );
return @res if ( $res[3] == 0 && !$rel_uri );
if ( defined $hr && ref($hr) ) {
$$hr{whisker}->{uri} = $res[0] if ( defined $res[0] );
if ( defined $res[4] ) {
$$hr{whisker}->{parameters} = $res[4];
}
else { delete $$hr{whisker}->{parameters}; }
return @res if ($rel_uri);
if ( $res[1] eq 'https' ) {
$$hr{whisker}->{ssl} = 1;
} else { $$hr{whisker}->{ssl} = 0; }
$$hr{whisker}->{host} = $res[2] if ( defined $res[2] );
$$hr{whisker}->{port} = $res[3];
if ( defined $res[6] ) {
$$hr{whisker}->{uri_user} = $res[6];
}
else { delete $$hr{whisker}->{uri_user}; }
if ( defined $res[7] ) {
$$hr{whisker}->{uri_password} = $res[7];
}
else { delete $$hr{whisker}->{uri_password}; }
}
return @res;
}
sub uri_join {
my @V = @_;
my $URL;
$URL .= $V[1] . ':' if defined $V[1];
if ( defined $V[2] ) {
$URL .= '//';
if ( defined $V[6] ) {
$URL .= $V[6];
$URL .= ':' . $V[7] if defined $V[7];
$URL .= '@';
}
$URL .= $V[2];
}
if ( $V[3] > 0 ) {
my $no = 0;
$no++ if ( $V[3] == 80  && defined $V[1] && $V[1] eq 'http' );
$no++ if ( $V[3] == 443 && defined $V[1] && $V[1] eq 'https' );
$URL .= ':' . $V[3] if ( !$no );
}
$URL .= $V[0];
$URL .= '?' . $V[4] if defined $V[4];
$URL .= '#' . $V[5] if defined $V[5];
return $URL;
}
sub uri_absolute {
my ( $uri, $buri, $norm ) = @_;
return undef if ( !defined $uri || !defined $buri );
return $uri if ( $uri =~ m#^[-+.a-z0-9A-Z]+://# );
if ( substr( $uri, 0, 1 ) eq '/' ) {
if ( $buri =~ m#^[-+.a-z0-9A-Z]+://# ) {
my @p = uri_split($buri);
$buri = "$p[1]://$p[2]";
$buri .= ":$p[3]" if ( ($p[1] eq 'http' && $p[3] != 80) ||
($p[1] eq 'https' && $p[3] != 443) );
}
else {    # ah suck, base URI isn't absolute...
return $uri;
}
}
else {
$buri =~ s/[?#].*$//;    # remove params and fragments
$buri .= '/' if ( $buri =~ m#^[a-z]+://[^/]+$#i );
$buri =~ s#/[^/]*$#/#;
}
return uri_normalize("$buri$uri")
if ( defined $norm && $norm > 0 );
return $buri . $uri;
}
sub uri_normalize {
my ( $host, $uri, $win ) = ( '', @_ );
$uri =~ tr#\\#/# if ( defined $win && $win > 0 );
if ( $uri =~ s#^([-+.a-z0-9A-Z]+:)## ) {
return undef if ( $1 ne 'http:' && $1 ne 'https:' );
$host = $1;
return undef unless ( $uri =~ s#^(//[^/]+)## );
$host .= $1;
}
return "$host/" if ( $uri eq '' || $uri eq '/' );
return "$host$uri" if ( index( $uri, '/.' ) < 0 );
my $extra = '';
$extra = $1 if($uri =~ s/([?#].*)$//);    # remove params and fragments
1 while ( $uri =~ s#/\./#/# || $uri =~ s#//#/# );
$uri =~ s#/\.$#/#;
1 while ( $uri =~ s#[^/]+/\.\./## );
1 while ( $uri =~ s#^/\.\./#/# );
$uri =~ s#[^/]*/\.\.$##;
$uri ||= '/';
return $host . $uri . $extra;
}
sub uri_get_dir {
my ( $w, $URL ) = ( 0, shift );
return undef if ( !defined $URL );
$URL = substr( $URL, 0, $w ) if ( ( $w = index( $URL, '#' ) ) >= 0 );
$URL = substr( $URL, 0, $w ) if ( ( $w = index( $URL, '?' ) ) >= 0 );
return $URL if ( substr( $URL, -1, 1 ) eq '/' );
if ( ( $w = rindex( $URL, '/' ) ) >= 0 ) {
$URL = substr( $URL, 0, $w + 1 );
}
else {
$URL = '';
}
return $URL;
}
sub uri_strip_path_parameters {
my ( $uri, $hr ) = @_;
my $s   = 0;
$s++ if ( defined $hr && ref($hr) );
my @p = split( /\//, $uri, -1 );
map {
if (s/;(.*)$//) { $$hr{$_} = $1 if ($s); }
} @p;
return join( '/', @p );
}
sub uri_parse_parameters {
my ( $str, $decode, $multi ) = @_;
my %P;
if( $str !~ tr/=&// ){
$P{$str} = undef;
return \%P;
}
$multi  ||= 0;
$decode ||= 0;
foreach ( split( /&/, $str ) ) {
my ( $name, $value ) = split( /=/, $_, 2 );
if ($decode) {
$name  = uri_unescape($name);
$value = uri_unescape($value);
}
if ( defined $P{$name} && $multi ) {
if ( ref( $P{$name} ) ) { push @{ $P{$name} }, $value; }
else { $P{$name} = [ $P{$name}, $value ]; }
}
else {
$P{$name} = $value;
}
}
return \%P;
}
sub uri_escape {
my $data = shift;
return undef if ( !defined $data );
$data =~ s/\%/\%25/g;
$data =~ s/([+?&=#;@\\\/])/sprintf("%%%02x",ord($1))/eg;
$data =~ tr/ /+/;
$data =~ s/([^!-~])/sprintf("%%%02x",ord($1))/eg;
return $data;
}
sub uri_unescape {
my $data = shift;
return undef if ( !defined $data );
$data =~ tr/+/ /;
$data =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
return $data;
}
sub utils_recperm {
my ( $d, $p, $pp, $pn, $r, $fr, $dr, $ar, $cr ) = ( '', shift, shift, @_ );
$p =~ s#/+#/#g;
if ( $pp >= @$pn ) {
push @$r, $p if &$cr( $$dr{$p} );
}
else {
my $c = $$pn[$pp];
if ( $c !~ /^\@/ ) {
utils_recperm( $p . $c . '/', $pp + 1, @_ )
if ( &$fr( $p . $c . '/' ) );
}
else {
$c =~ tr/\@//d;
if ( defined $$ar{$c} ) {
foreach $d ( @{ $$ar{$c} } ) {
if ( &$fr( $p . $d . '/' ) ) {
utils_recperm( $p . $d . '/', $pp + 1, @_ );
}
}
}
}
}
}
sub utils_array_shuffle {    # fisher yates shuffle....w00p!
my $array = shift;
my $i;
for ( $i = @$array ; --$i ; ) {
my $j = int rand( $i + 1 );
next if $i == $j;
@$array[ $i, $j ] = @$array[ $j, $i ];
}
}    # end array_shuffle, from Perl Cookbook (rock!)
sub utils_randstr {
my $str;
my $drift = shift || ( ( rand() * 10 ) % 10 ) + 10;
my $CHARS = shift
|| 'abcdefghijklmnopqrstuvwxyz'
. 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
. '0123456789';
my $L = length($CHARS);
for ( 1 .. $drift ) {
$str .= substr( $CHARS, ( ( rand() * $L ) % $L ), 1 );
}
return $str;
}
sub utils_port_open {    # this should be platform-safe
my ( $target, $port ) = @_;
return 0 if ( !defined $target || !defined $port );
return 0 if ( !defined $Socket::VERSION );
if ( !( socket( S, PF_INET, SOCK_STREAM, 0 ) ) ) { return 0; }
if ( connect( S, sockaddr_in( $port, inet_aton($target) ) ) ) {
close(S);
return 1;
}
else { return 0; }
}
sub utils_lowercase_keys {
my $href = shift;
return if ( !( defined $href && ref($href) ) );
my $count = 0;
while ( my ( $key, $val ) = each %$href ) {
if ( $key =~ tr/A-Z// ) {
$count++;
delete $$href{$key};
$$href{ lc($key) } = $val;
}
}
return $count;
}
sub utils_find_lowercase_key {
return utils_find_key( $_[0], $_[1], 1 );
}
sub utils_find_key {
my ( $href, $key, $dolower ) = ( shift, shift, shift || 0 );
return undef if ( !( defined $href && ref($href) ) );
return undef if ( !defined $key );
if ($dolower) {
$key = lc($key);
my ( $k, $v );
my @match;
while ( ( $k, $v ) = each %$href ) {
if ( lc($k) eq $key ) {
if( ref($v) ) {
push @match, @$v;
} else {
push @match, $v;
}
}
}
return @match if wantarray();
return \@match if( ~~@match > 1 );
return $match[0];
}
else {
return @{ $href->{$key} } if ( ref( $href->{$key} ) && wantarray() );
return $href->{$key};
}
return undef;
}
sub utils_delete_lowercase_key {
my ( $href, $key ) = ( shift, lc(shift) );
return undef if ( !( defined $href && ref($href) ) );
return undef if ( !defined $key );
my $deleted = 0;
foreach ( keys %$href ) {
if ( lc($_) eq $key ) {
delete $href->{$_};
$deleted++;
}
}
return $deleted;
}
{
my $POS = 0;
sub utils_getline {
my ( $dr, $rp ) = @_;
return undef if ( !( defined $dr && ref($dr) ) );
$POS = $rp if ( defined $rp );
my $where = index( $$dr, "\x0a", $POS );
return undef if ( $where == -1 );
my $str = substr( $$dr, $POS, $where - $POS );
$POS = $where + 1;
return $str;
}
}
{
my $POS = 0;
sub utils_getline_crlf {
my ( $dr, $rp ) = @_;
return undef if ( !( defined $dr && ref($dr) ) );
$POS = $rp if ( defined $rp );
my $tpos = $POS;
while (1) {
my $where = index( $$dr, "\x0a", $tpos );
return undef if ( $where == -1 );
if ( substr( $$dr, $where - 1, 1 ) eq "\x0d" ) {
my $str = substr( $$dr, $POS, $where - $POS - 1 );
$POS = $where + 1;
return $str;
}
else {
$tpos = $where + 1;
}
}
}
}
sub utils_save_page {
my ( $file, $hr ) = @_;
return 1 if ( !ref($hr) || ref($file) );
return 0
if ( !defined $$hr{'whisker'}
|| !defined $$hr{'whisker'}->{'data'} );
open( OUT, ">$file" ) || return 1;
binmode(OUT); # Stupid Windows
print OUT $$hr{'whisker'}->{'data'};
close(OUT);
return 0;
}
sub utils_getopts {
my ( $str, $ref ) = @_;
my ( %O, $l );
my @left;
return 1 if ( $str =~ tr/-:a-zA-Z0-9//c );
while ( $str =~ m/([a-z0-9]:{0,1})/ig ) {
$l = $1;
if ( $l =~ tr/://d ) {
$O{$l} = 1;
}
else { $O{$l} = 0; }
}
while ( $l = shift(@ARGV) ) {
push( @left, $l ) && next if ( substr( $l, 0, 1 ) ne '-' );
push( @left, $l ) && next if ( $l eq '-' );
substr( $l, 0, 1 ) = '';
if ( length($l) != 1 ) {
%$ref = ();
return 1;
}
if ( $O{$l} == 1 ) {
my $x = shift(@ARGV);
$$ref{$l} = $x;
}
else { $$ref{$l} = 1; }
}
@ARGV = @left;
return 0;
}
sub utils_text_wrapper {
my ( $out, $w, $str, $crlf, $width ) = ( '', 0, @_ );
$crlf  ||= "\n";
$width ||= 76;
$str .= $crlf if ( $str !~ /$crlf$/ );
return $str if ( length($str) <= $width );
while ( length($str) > $width ) {
my $w1 = rindex( $str, ' ',  $width );
my $w2 = rindex( $str, "\t", $width );
if ( $w1 > $w2 ) { $w = $w1; }
else { $w = $w2; }
if ( $w == -1 ) {
$w = $width;
}
else { substr( $str, $w, 1 ) = ''; }
$out .= substr( $str, 0, $w, '' );
$out .= $crlf;
}
return $out . $str;
}
sub utils_bruteurl {
my ( $hin, $upre, $upost, $arin, $arout ) = @_;
my ( $U, %hout );
return if ( !( defined $hin   && ref($hin) ) );
return if ( !( defined $arin  && ref($arin) ) );
return if ( !( defined $arout && ref($arout) ) );
return if ( !defined $upre  || length($upre) == 0 );
return if ( !defined $upost || length($upost) == 0 );
http_fixup_request($hin);
map {
( $U = $_ ) =~ tr/\r\n//d;
next if ( $U eq '' );
if (
!http_do_request( $hin, \%hout, { 'uri' => $upre . $U . $upost } ) )
{
if (   $hout{'whisker'}->{'code'} == 200
|| $hout{'whisker'}->{'code'} == 403 )
{
push( @{$arout}, $U );
}
}
} @$arin;
}
sub utils_join_tag {
my ( $name, $href ) = @_;
return undef if ( !defined $name || $name eq '' );
return undef if ( !defined $href || !ref($href) );
my ( $out, $k, $v ) = ( "<$name", '', '' );
while ( ( $k, $v ) = each %$href ) {
next if ( $k eq '' );
$out .= " $k";
$out .= "=\"$v\"" if ( defined $v );
}
$out .= '>';
return $out;
}
sub utils_request_clone {
my ( $from, $to ) = @_;
return 0 if ( !defined $from || !ref($from) );
return 0 if ( !defined $to   || !ref($to) );
return 0 if ( !defined $from->{whisker}->{MAGIC} );
%$to = ();
my ( $k, $v );
while ( ( $k, $v ) = each(%$from) ) {
next if ( $k eq 'whisker' );
if ( ref($v) ) {
@{ $to->{$k} } = @$v;
}
else {
$to->{$k} = $v;
}
}
$to->{whisker} = {};
while ( ( $k, $v ) = each( %{ $from->{whisker} } ) ) {
if ( ref($v) ) {
@{ $to->{whisker}->{$k} } = @$v;
}
else {
$to->{whisker}->{$k} = $v;
}
}
return 1;
}
sub utils_request_fingerprint {
my ( $href, $hash ) = @_;
$hash ||= 'md5';
return undef if ( !defined $href || !ref($href) );
return undef if ( !defined $href->{whisker}->{MAGIC} );
my $data = '';
if ( $href->{whisker}->{MAGIC} == 31339 ) {    # LW2 request
$data = http_req2line($href);
if ( $href->{whisker}->{version} ne '0.9' ) {
$data .= http_construct_headers($href);
$data .= $href->{whisker}->{raw_header_data}
if ( defined $href->{whisker}->{raw_header_data} );
$data .= $href->{whisker}->{http_eol};
$data .= $href->{whisker}->{data}
if ( defined $href->{whisker}->{data} );
}                                          # http 0.9 support
return 'md5:' . md5($data) if ( $hash eq 'md5' );
return 'md4:' . md4($data) if ( $hash eq 'md4' );
}
return undef;
}
sub utils_flatten_lwhash {
my $hr = shift;
return undef if ( !defined $hr || !ref($hr) );
my $out;
if ( $hr->{whisker}->{MAGIC} == 31339 ) {
$out = http_req2line($hr);
}
elsif ( $hr->{whisker}->{MAGIC} == 31340 ) {
$out = http_resp2line($hr);
}
else {
return undef;
}
$out .= http_construct_headers($hr);
$out .= $hr->{whisker}->{http_eol} || "\x0d\x0a";
if ( defined $hr->{whisker}->{data}
&& length( $hr->{whisker}->{data} ) > 0 )
{
$out .= $hr->{whisker}->{data};
}
return $out;
}
sub _utils_carp_common {
my ($x,$pack,$m) = (0, shift || '',join('',@_) || '(Unknown error)');
my @s = caller($x++);
@s=caller($x++) while(defined $s[0] && ($s[0] eq 'LW2' || $s[0] eq $pack));
return $m if !defined $s[0];
return "$m at $s[1] line $s[2]\n";
}
sub utils_carp {
warn _utils_carp_common(@_);
}
sub utils_croak {
die _utils_carp_common(@_);
}
1;
