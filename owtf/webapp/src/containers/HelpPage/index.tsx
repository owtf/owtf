import React from "react";
import { BiMenuAltLeft } from "react-icons/bi";
import { BsCalculator } from "react-icons/bs";
import { GoSearch } from "react-icons/go";
import { IoHelpCircleSharp } from "react-icons/io5";
import { RiBookletFill } from "react-icons/ri";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";

type HelpLink = {
  id: number;
  text: string;
  link: string;
};

const exploitationLinks: HelpLink[] = [
  { id: 1, text: "Hackvertor", link: "http://hackvertor.co.uk/public" },
  { id: 2, text: "ExploitDB", link: "http://www.exploit-db.com/" },
  { id: 3, text: "ExploitSearch", link: "http://www.exploitsearch.net/" },
  { id: 4, text: "Hackipedia", link: "http://www.hakipedia.com/index.php/Hakipedia" },
];

const methodologyLinks: HelpLink[] = [
  {
    id: 1,
    text: "OWASP",
    link: "https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents",
  },
  { id: 2, text: "Pentest Standard", link: "http://www.exploit-db.com/" },
  { id: 3, text: "OSSTMM", link: "http://www.isecom.org/research/osstmm.html" },
];

const calculatorLinks: HelpLink[] = [
  {
    id: 1,
    text: "CVSS Advanced",
    link: "http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2",
  },
  {
    id: 2,
    text: "CVSS Normal",
    link: "http://nvd.nist.gov/cvss.cfm?calculator&version=2",
  },
];

const learnTestLinks: HelpLink[] = [
  {
    id: 1,
    text: "OWASP VWAD",
    link: "http://www.owasp.org/index.php?title=OWASP_Vulnerable_Web_Applications_Directory_Project",
  },
  {
    id: 2,
    text: "Securitythoughts",
    link: "http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/",
  },
  {
    id: 3,
    text: "Danielmiessler",
    link: "http://danielmiessler.com/projects/webappsec_testing_resources/",
  },
];

const owtfHelpLinks: HelpLink[] = [
  { id: 1, text: "Github Wiki", link: "https://github.com/owtf/owtf/wiki" },
  { id: 2, text: "Youtube channel", link: "http://www.youtube.com/user/owtfproject" },
  { id: 3, text: "Release notes", link: "http://blog.7-a.org/search/label/OWTF%20Release" },
  { id: 4, text: "Github repository", link: "https://github.com/owtf/owtf" },
  { id: 5, text: "Issue tracker", link: "https://github.com/owtf/owtf/issues" },
  { id: 6, text: "Mailing List", link: "https://lists.owasp.org/mailman/listinfo/owasp_owtf" },
  { id: 7, text: "Twitter", link: "https://twitter.com/owtfp" },
  { id: 8, text: "Medium Blog", link: "https://medium.com/@owtf" },
  { id: 9, text: "Author's blog", link: "http://blog.7-a.org" },
];

function ResourceCard({
  title,
  links,
  icon,
}: {
  title: string;
  links: HelpLink[];
  icon: React.ReactNode;
}) {
  return (
    <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-xl font-semibold tracking-tight">
          <span className="text-zinc-500 dark:text-zinc-300">{icon}</span>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {links.map((obj) => (
            <li key={obj.id}>
              <a
                href={obj.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-zinc-700 transition hover:text-zinc-900 hover:underline dark:text-zinc-200 dark:hover:text-zinc-100"
              >
                {obj.text}
              </a>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export default class Help extends React.Component {
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <div className="mx-auto w-full max-w-[1240px] space-y-6 px-4 py-6" data-test="helpComponent">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">Help Center</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            Security references and OWTF project resources in one place.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <ResourceCard title="Exploitation" links={exploitationLinks} icon={<GoSearch />} />
          <ResourceCard title="Methodology" links={methodologyLinks} icon={<BiMenuAltLeft />} />
          <ResourceCard title="Calculators" links={calculatorLinks} icon={<BsCalculator />} />
          <ResourceCard title="Test/Learn" links={learnTestLinks} icon={<RiBookletFill />} />
        </div>

        <ResourceCard title="OWTF Help Links" links={owtfHelpLinks} icon={<IoHelpCircleSharp />} />
      </div>
    );
  }
}
