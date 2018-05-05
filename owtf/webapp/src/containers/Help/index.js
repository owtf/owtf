/*
 * Help
 */
import React from 'react';
import {Grid, Panel, Col, Row} from 'react-bootstrap';


export default class Help extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    const exploitationLinks = [
      {'id': 1, 'text': "Hackvertor", 'link': "http://hackvertor.co.uk/public"},
      {'id': 2, 'text': "ExploitDB", 'link': "http://www.exploit-db.com/"},
      {'id': 3, 'text': "ExploitSearch", 'link': "http://www.exploitsearch.net/"},
      {'id': 4, 'text': "Hackipedia", 'link': "http://www.hakipedia.com/index.php/Hakipedia"},
    ];

    const methodologyLinks = [
      {'id': 1, 'text': "OWASP", 'link': "https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents"},
      {'id': 2, 'text': "Pentest Standard", 'link': "http://www.exploit-db.com/"},
      {'id': 3, 'text': "OSSTMM", 'link': "http://www.isecom.org/research/osstmm.html"},
    ];

    const calculatorLinks = [
      {'id': 1, 'text': "CVSS Advanced", 'link': "http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2"},
      {'id': 2, 'text': "CVSS Normal", 'link': "http://nvd.nist.gov/cvss.cfm?calculator&version=2"},
    ];

    const learnTestLinks = [
      {'id':1, 'text': "OWASP VWAD", 'link': "http://www.owasp.org/index.php?title=OWASP_Vulnerable_Web_Applications_Directory_Project"},
      {'id':2, 'text': "Securitythoughts", 'link': "http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/" },
      {'id':3, 'text': "Danielmiessler", 'link': "http://danielmiessler.com/projects/webappsec_testing_resources/"}
    ];

    const owtfHelpLinks = [
      [
        {'id': 1, 'text': "Github Wiki", 'link': "https://github.com/owtf/owtf/wiki"},
        {'id': 2, 'text': "Youtube channel", 'link': "http://www.youtube.com/user/owtfproject"},
        {'id': 3, 'text': "Release notes", 'link': "http://blog.7-a.org/search/label/OWTF%20Release"}
      ],
      [
        {'id': 1, 'text': "Github repository", 'link': "https://github.com/owtf/owtf"},
        {'id': 2, 'text': "Issue tracker", 'link': "https://github.com/owtf/owtf/issues"},
      ],
      [
        {'id': 1, 'text': "Mailing List", 'link': "https://lists.owasp.org/mailman/listinfo/owasp_owtf"},
        {'id': 2, 'text': "Twitter", 'link': "https://twitter.com/owtfp"},
        {'id': 3, 'text': "Medium Blog", 'link': "https://medium.com/@owtf"},
        {'id': 4, 'text': "Author's blog", 'link': "http://blog.7-a.org"}
      ]
    ];

    return (
      <Grid>
        <Row>
          <Col xs={6} md={4}>
              <Panel>
                <Panel.Heading>Exploitation</Panel.Heading>
                <Panel.Body>
                  <ul>
                    {exploitationLinks.map(function(obj){
                        return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                    })}
                  </ul>
                </Panel.Body>
              </Panel>
          </Col>
          <Col xs={6} md={4}>
            <Panel>
              <Panel.Heading>
                <Panel.Title componentClass="h3">Methodology</Panel.Title>
              </Panel.Heading>
              <Panel.Body>
                  <ul>
                    {methodologyLinks.map(function(obj){
                      return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                    })}
                  </ul>
              </Panel.Body>
            </Panel>
          </Col>
          <Col xsHidden md={4}>
            <Panel>
              <Panel.Heading>
                <Panel.Title componentClass="h3">Calculators</Panel.Title>
              </Panel.Heading>
              <Panel.Body>
                  <ul>
                    {calculatorLinks.map(function(obj){
                      return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                    })}
                  </ul>
              </Panel.Body>
            </Panel>
          </Col>
        </Row>
        <Row>
          <Col xs={6} md={6}>
              <Panel>
                <Panel.Heading>Test/Learn</Panel.Heading>
                <Panel.Body>
                  <ul>
                    {learnTestLinks.map(function(obj){
                      return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                    })}
                  </ul>
                </Panel.Body>
              </Panel>
          </Col>
          <Col xs={6} md={6}>
            <Panel>
              <Panel.Heading>
                <Panel.Title componentClass="h3">OWTF Help Links</Panel.Title>
              </Panel.Heading>
              <Panel.Body>
                <Row>
                  <Col xs={6} md={4}>
                    <ul>
                      {owtfHelpLinks[0].map(function(obj){
                          return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                      })}
                    </ul>
                  </Col>
                  <Col xs={6} md={4}>
                    <ul>
                      {owtfHelpLinks[1].map(function(obj){
                          return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                      })}
                    </ul>
                  </Col>
                  <Col xs={6} md={4}>
                    <ul>
                      {owtfHelpLinks[2].map(function(obj){
                          return <li key={obj.id}><a href={obj.link} target='_blank'>{obj.text}</a></li>;
                      })}
                    </ul>
                  </Col>
                </Row>
              </Panel.Body>
            </Panel>
          </Col>
        </Row>
      </Grid>
    )
  }
}
