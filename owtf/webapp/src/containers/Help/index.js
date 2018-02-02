import React, { Component, PropTypes } from 'react';

import { Grid, Row, Col } from 'react-flexbox-grid';
import './index.scss';


export default class Help extends Component {
  render() {
    return (
    <div>
    <Grid fluid>
        <Row>
            <Col xs={6} sm={6} md={12} lg={12}>
            <div className="panel panel-info span3">
                <div className="panel-heading">
                    <div className="panel-title"><i className="fa fa-search"></i> Exploitation</div>
                </div>
                <div className="panel-body">
                    <ul>
                        <li><a href="http://hackvertor.co.uk/public" target="_blank"> Hackvertor </a></li>
                        <li><a href="http://www.exploit-db.com/" target="_blank"> ExploitDB </a></li>
                        <li><a href="http://www.exploitsearch.net/" target="_blank"> ExploitSearch </a></li>
                        <li><a href="http://www.hakipedia.com/index.php/Hakipedia" target="_blank"> Hackipedia </a></li>
                    </ul>
                </div>
            </div>
            <div className="panel panel-info span3">
                <div className="panel-heading">
                    <div className="panel-title"><i className="fa fa-road"></i> Methodology</div>
                </div>
                <div className="panel-body">
                    <ul>
                        <li><a href="https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents" target="_blank"> OWASP </a></li>
                        <li><a href="http://www.pentest-standard.org/index.php/Main_Page" target="_blank"> Pentest Standard </a></li>
                        <li><a href="http://www.isecom.org/research/osstmm.html" target="_blank"> OSSTMM </a></li>
                    </ul>
                </div>
            </div>
            <div className="panel panel-info span3">
                <div className="panel-heading">
                    <div className="panel-title"><i className="fa fa-plus-circle"></i> Calculators</div>
                </div>
                <div className="panel-body">
                    <ul>
                        <li><a href="http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2" target="_blank"> CVSS Advanced </a></li>
                        <li><a href="http://nvd.nist.gov/cvss.cfm?calculator&version=2" target="_blank"> CVSS Normal </a></li>
                    </ul>
                </div>
            </div>
            <div className="panel panel-info span3">
                <div className="panel-heading">
                    <div className="panel-title"><i className="fa fa-book"></i> Test/Learn</div>
                </div>
                <div className="panel-body">
                    <ul>
                        <li><a href="http://www.owasp.org/index.php?title=OWASP_Vulnerable_Web_Applications_Directory_Project" target="_blank"> OWASP VWAD </a></li>
                        <li><a href="http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/" target="_blank"> Securitythoughts </a></li>
                        <li><a href="http://danielmiessler.com/projects/webappsec_testing_resources/" target="_blank"> Danielmiessler </a></li>
                    </ul>
                </div>
            </div>
            </Col>
        </Row>
    </Grid>
    <Grid>
            <Col xs={6} sm={6} md={12} lg={12}>
            <div className="panel panel-default">
                <div className="panel-heading">
                    <div className="panel-title"><i className="fa fa-gear"></i> OWTF Help Links</div>
                </div>
                <div className="panel-body">
                    <div className="col-md-2">
                    </div>
                    <div className="col-md-3">
                        <strong>Useful Links</strong>
                        <ul className="list-unstyled">
                            <li><i className="fa fa-github-alt"></i><a href="https://github.com/owtf/owtf/wiki" target="__blank"> Github wiki</a></li>
                            <li><i className="fa fa-youtube-play"></i><a href="http://www.youtube.com/user/owtfproject" target="__blank"> Youtube Channel</a></li>
                            <li><i className="fa fa-file-text-o"></i><a href="http://blog.7-a.org/search/label/OWTF%20Release" target="__blank"> Release notes</a></li>
                        </ul>
                    </div>
                    <div className="col-md-3">
                        <strong>Contributor's Links</strong>
                        <ul className="list-unstyled">
                            <li><i className="fa fa-github-square"></i><a href="https://github.com/owtf/owtf" target="__blank"> Github Repo</a></li>
                            <li><i className="fa fa-exclamation-circle"></i><a href="https://github.com/owtf/owtf/issues" target="__blank"> Report an Issue</a></li>
                            <li><i className="fa fa-file"></i><a href="https://github.com/owtf/owtf/wiki/Contributor%27s-README" target="__blank"> Readme</a></li>
                            <li><i className="fa fa-user"></i><a href="https://github.com/owtf/owtf/blob/master/AUTHORS" target="__blank"> Contributors</a></li>
                        </ul>
                    </div>
                    <div className="col-md-3">
                        <strong>Stay in touch</strong>
                        <ul className="list-unstyled">
                            <li><i className="fa fa-comments-o"></i><a href="http://irc.netsplit.de/channels/details.php?room=%23owtf&net=freenode" target="__blank"> IRC Channel</a></li>
                            <li><i className="fa fa-envelope"></i><a href="https://lists.owasp.org/mailman/listinfo/owasp_owtf" target="__blank"> Mailing List</a></li>
                            <li><i className="fa fa-twitter"></i><a href="https://twitter.com/owtfp" target="__blank"> Twitter</a></li>
                            <li><i className="fa fa-bookmark-o"></i><a href="http://blog.7-a.org" target="_blank" > Author's Blog</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            </Col>
    </Grid>
    </div>
    );
  }
}
