/*
 * HelpPage
 */
import React from "react";
import { RiBookletFill } from "react-icons/ri";
import { BsCalculator } from "react-icons/bs";
import { GoSearch } from "react-icons/go";
import { IoHelpCircleSharp } from "react-icons/io5";
import { BiMenuAltLeft } from "react-icons/bi";

export default class Help extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    const exploitationLinks = [
      { id: 1, text: "Hackvertor", link: "http://hackvertor.co.uk/public" },
      { id: 2, text: "ExploitDB", link: "http://www.exploit-db.com/" },
      { id: 3, text: "ExploitSearch", link: "http://www.exploitsearch.net/" },
      {
        id: 4,
        text: "Hackipedia",
        link: "http://www.hakipedia.com/index.php/Hakipedia"
      }
    ];

    const methodologyLinks = [
      {
        id: 1,
        text: "OWASP",
        link:
          "https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents"
      },
      { id: 2, text: "Pentest Standard", link: "http://www.exploit-db.com/" },
      {
        id: 3,
        text: "OSSTMM",
        link: "http://www.isecom.org/research/osstmm.html"
      }
    ];

    const calculatorLinks = [
      {
        id: 1,
        text: "CVSS Advanced",
        link: "http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2"
      },
      {
        id: 2,
        text: "CVSS Normal",
        link: "http://nvd.nist.gov/cvss.cfm?calculator&version=2"
      }
    ];

    const learnTestLinks = [
      {
        id: 1,
        text: "OWASP VWAD",
        link:
          "http://www.owasp.org/index.php?title=OWASP_Vulnerable_Web_Applications_Directory_Project"
      },
      {
        id: 2,
        text: "Securitythoughts",
        link:
          "http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/"
      },
      {
        id: 3,
        text: "Danielmiessler",
        link: "http://danielmiessler.com/projects/webappsec_testing_resources/"
      }
    ];

    const owtfHelpLinks = [
      [
        {
          id: 1,
          text: "Github Wiki",
          link: "https://github.com/owtf/owtf/wiki"
        },
        {
          id: 2,
          text: "Youtube channel",
          link: "http://www.youtube.com/user/owtfproject"
        },
        {
          id: 3,
          text: "Release notes",
          link: "http://blog.7-a.org/search/label/OWTF%20Release"
        }
      ],
      [
        {
          id: 1,
          text: "Github repository",
          link: "https://github.com/owtf/owtf"
        },
        {
          id: 2,
          text: "Issue tracker",
          link: "https://github.com/owtf/owtf/issues"
        }
      ],
      [
        {
          id: 1,
          text: "Mailing List",
          link: "https://lists.owasp.org/mailman/listinfo/owasp_owtf"
        },
        { id: 2, text: "Twitter", link: "https://twitter.com/owtfp" },
        { id: 3, text: "Medium Blog", link: "https://medium.com/@owtf" },
        { id: 4, text: "Author's blog", link: "http://blog.7-a.org" }
      ]
    ];

    return (
      <div className="helpPageContainer" data-test="helpComponent">
        <div
          className="helpPageContainer__exploitationContainer"
          data-test="helpBox"
        >
          <div className="helpPageContainer__exploitationContainer__headingContainer">
            <span>
              <GoSearch />
            </span>
            <h2>Exploitation</h2>
          </div>

          <div className="helpPageContainer__exploitationContainer__linksContainer">
            <ul>
              {exploitationLinks.map(obj => (
                <li key={obj.id}>
                  <a href={obj.link} target="_blank" rel="noopener noreferrer">
                    {obj.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div
          className="helpPageContainer__methodologyContainer"
          data-test="helpBox"
        >
          <div className="helpPageContainer__methodologyContainer__headingContainer">
            <span>
              <BiMenuAltLeft />
            </span>
            <h2>Methodology</h2>
          </div>

          <div className="helpPageContainer__methodologyContainer__linksContainer">
            <ul>
              {methodologyLinks.map(obj => (
                <li key={obj.id}>
                  <a href={obj.link} target="_blank" rel="noopener noreferrer">
                    {obj.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div
          className="helpPageContainer__calculatorsContainer"
          data-test="helpBox"
        >
          <div className="helpPageContainer__calculatorsContainer__headingContainer">
            <span>
              <BsCalculator />
            </span>
            <h2>Calculators</h2>
          </div>

          <div className="helpPageContainer__calculatorsContainer__linksContainer">
            <ul>
              {calculatorLinks.map(obj => (
                <li key={obj.id}>
                  <a href={obj.link} target="_blank" rel="noopener noreferrer">
                    {obj.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div
          className="helpPageContainer__testLearnContainer"
          data-test="helpBox"
        >
          <div className="helpPageContainer__testLearnContainer__headingContainer">
            <span>
              <RiBookletFill />
            </span>
            <h2>Test/Learn</h2>
          </div>

          <div className="helpPageContainer__testLearnContainer__linksContainer">
            <ul>
              {learnTestLinks.map(obj => (
                <li key={obj.id}>
                  <a href={obj.link} target="_blank" rel="noopener noreferrer">
                    {obj.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div
          className="helpPageContainer__helpLinksContainer"
          data-test="helpBox"
        >
          <div className="helpPageContainer__helpLinksContainer__headingContainer">
            <span>
              <IoHelpCircleSharp />
            </span>
            <h2>OWTF Help Links</h2>
          </div>

          <div className="helpPageContainer__helpLinksContainer__linksWrapper">
            <div className="helpPageContainer__helpLinksContainer__linksWrapper__linksContainer">
              <ul>
                {owtfHelpLinks[0].map(obj => (
                  <li key={obj.id}>
                    <a
                      href={obj.link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {obj.text}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div className="helpPageContainer__helpLinksContainer__linksWrapper__linksContainer">
              <ul>
                {owtfHelpLinks[1].map(obj => (
                  <li key={obj.id}>
                    <a
                      href={obj.link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {obj.text}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div className="helpPageContainer__helpLinksContainer__linksWrapper__linksContainer">
              <ul>
                {owtfHelpLinks[2].map(obj => (
                  <li key={obj.id}>
                    <a
                      href={obj.link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {obj.text}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
