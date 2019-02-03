/*
 * HelpPage
 */
import React from 'react';
import { Pane, Text, Heading, Icon } from 'evergreen-ui';


export default class Help extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    const exploitationLinks = [
      { id: 1, text: 'Hackvertor', link: 'http://hackvertor.co.uk/public' },
      { id: 2, text: 'ExploitDB', link: 'http://www.exploit-db.com/' },
      { id: 3, text: 'ExploitSearch', link: 'http://www.exploitsearch.net/' },
      { id: 4, text: 'Hackipedia', link: 'http://www.hakipedia.com/index.php/Hakipedia' },
    ];

    const methodologyLinks = [
      { id: 1, text: 'OWASP', link: 'https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents' },
      { id: 2, text: 'Pentest Standard', link: 'http://www.exploit-db.com/' },
      { id: 3, text: 'OSSTMM', link: 'http://www.isecom.org/research/osstmm.html' },
    ];

    const calculatorLinks = [
      { id: 1, text: 'CVSS Advanced', link: 'http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2' },
      { id: 2, text: 'CVSS Normal', link: 'http://nvd.nist.gov/cvss.cfm?calculator&version=2' },
    ];

    const learnTestLinks = [
      { id: 1, text: 'OWASP VWAD', link: 'http://www.owasp.org/index.php?title=OWASP_Vulnerable_Web_Applications_Directory_Project' },
      { id: 2, text: 'Securitythoughts', link: 'http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/' },
      { id: 3, text: 'Danielmiessler', link: 'http://danielmiessler.com/projects/webappsec_testing_resources/' },
    ];

    const owtfHelpLinks = [
      [
        { id: 1, text: 'Github Wiki', link: 'https://github.com/owtf/owtf/wiki' },
        { id: 2, text: 'Youtube channel', link: 'http://www.youtube.com/user/owtfproject' },
        { id: 3, text: 'Release notes', link: 'http://blog.7-a.org/search/label/OWTF%20Release' },
      ],
      [
        { id: 1, text: 'Github repository', link: 'https://github.com/owtf/owtf' },
        { id: 2, text: 'Issue tracker', link: 'https://github.com/owtf/owtf/issues' },
      ],
      [
        { id: 1, text: 'Mailing List', link: 'https://lists.owasp.org/mailman/listinfo/owasp_owtf' },
        { id: 2, text: 'Twitter', link: 'https://twitter.com/owtfp' },
        { id: 3, text: 'Medium Blog', link: 'https://medium.com/@owtf' },
        { id: 4, text: "Author's blog", link: 'http://blog.7-a.org' },
      ],
    ];

    return (
      <Pane clearfix display="flex" flexDirection="row" flexWrap= "wrap" justifyContent="center">
        <Pane
          elevation={1}
          width={350}
          margin={20}
          display="flex"
          flexDirection="column"
        >
          <Heading height={40} background="#e1eaea">
            <Pane margin={10}><Icon icon="search"/> Exploitation </Pane>
          </Heading>
          <Text margin={20}>
            <ul>
              {exploitationLinks.map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
            </ul>
          </Text>
        </Pane>
        <Pane
          elevation={1}
          width={350}
          margin={20}
          display="flex"
          flexDirection="column"
        >
          <Heading height={40} background="#e1eaea">
            <Pane margin={10}><Icon icon="horizontal-bar-chart-desc"/> Methodology </Pane>
          </Heading>
          <Text margin={20}>
            <ul>
              {methodologyLinks.map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
            </ul>
          </Text>
        </Pane>
        <Pane
          elevation={1}
          width={350}
          margin={20}
          display="flex"
          flexDirection="column"
        >
          <Heading height={40} background="#e1eaea">
            <Pane margin={10}><Icon icon="calculator"/> Calculators </Pane>
          </Heading>
          <Text margin={20}>
            <ul>
              {calculatorLinks.map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
            </ul>
          </Text>
        </Pane>
        <Pane
          elevation={1}
          width={500}
          margin={20}
          display="flex"
          flexDirection="column"
        >
          <Heading height={40} background="#e1eaea">
            <Pane margin={10}><Icon icon="book"/> Test/Learn </Pane>
          </Heading>
          <Text margin={20}>
            <ul>
              {learnTestLinks.map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
            </ul>
          </Text>
        </Pane>
        <Pane
          elevation={1}
          width={600}
          margin={20}
          display="flex"
          flexDirection="column"
        >
          <Heading height={40} background="#e1eaea">
            <Pane margin={10}><Icon icon="help"/> OWTF Help Links </Pane>
          </Heading>
          <Pane display="flex" flexDirection="row">
            <Pane display="flex" flexDirection="column">
              <Text margin={20}>
                <ul>
                  {owtfHelpLinks[0].map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
                </ul>
              </Text>
            </Pane>
            <Pane display="flex" flexDirection="column">
              <Text margin={20}>
                <ul>
                  {owtfHelpLinks[1].map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
                </ul>
              </Text>
            </Pane>
            <Pane display="flex" flexDirection="column">
              <Text margin={20}>
                <ul>
                  {owtfHelpLinks[2].map(obj => <li key={obj.id}><a href={obj.link} target="_blank">{obj.text}</a></li>)}
                </ul>
              </Text>
            </Pane>
          </Pane>
        </Pane>
      </Pane>
    );
  }
}
