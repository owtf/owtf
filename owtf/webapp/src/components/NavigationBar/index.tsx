import React from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, Moon, Sun } from "lucide-react";
import { Button } from "../ui/button";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "../ui/navigation-menu";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "../ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";

const logo = "/img/logo.png";

interface NavigationBarPropsType {
  brand: any;
  links: any[];
}

interface NavigationBarStateType {
  theme: "light" | "dark";
}

type NavLinkItem = {
  linkTo?: string;
  text: string;
  dropdown?: boolean;
  links?: Array<{ linkTo: string; text: string }>;
};

const Logo = ({ brand }: { brand: any }) => (
  <Link
    to={brand.linkTo}
    className="inline-flex items-center gap-2.5 whitespace-nowrap text-zinc-900 dark:text-zinc-100"
  >
    <span className="text-3xl font-semibold tracking-tight">{brand.text}</span>
    <img src={logo} alt="owtf logo" className="h-7 w-7 rounded-full object-cover" />
  </Link>
);

const DesktopNavMenu = ({ links }: { links: NavLinkItem[] }) => (
  <NavigationMenu className="hidden md:block">
    <NavigationMenuList>
      {links.map((link) => {
        if (link.dropdown || !link.linkTo) {
          return null;
        }

        return (
          <NavigationMenuItem key={link.linkTo}>
            <NavigationMenuLink asChild className={navigationMenuTriggerStyle()}>
              <NavLink
                to={link.linkTo}
                activeClassName="border-zinc-300 bg-zinc-100 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                className={navigationMenuTriggerStyle()}
              >
                {link.text}
              </NavLink>
            </NavigationMenuLink>
          </NavigationMenuItem>
        );
      })}
    </NavigationMenuList>
  </NavigationMenu>
);

const MobileNavigationSheet = ({ links }: { links: NavLinkItem[] }) => (
  <Sheet>
    <SheetTrigger asChild>
      <Button size="icon" variant="outline" aria-label="Open navigation menu">
        <Menu className="h-4 w-4" />
      </Button>
    </SheetTrigger>
      <SheetContent side="right" className="px-4 py-3">
        <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
      <div className="mb-5 border-b border-zinc-200 pb-4 dark:border-zinc-800">
        <Logo brand={{ linkTo: "/", text: "OWASP OWTF" }} />
      </div>
      <nav className="flex flex-col gap-2">
        {links.map((link) => {
          if (link.dropdown || !link.linkTo) {
            return null;
          }
          return (
            <Button key={link.linkTo} asChild variant="ghost" className="justify-start">
              <Link to={link.linkTo}>{link.text}</Link>
            </Button>
          );
        })}
      </nav>
    </SheetContent>
  </Sheet>
);

export default class NavigationBar extends React.Component<NavigationBarPropsType, NavigationBarStateType> {
  constructor(props) {
    super(props);
    this.state = {
      theme: "light",
    };
  }

  componentDidMount() {
    const storedTheme = localStorage.getItem("owtf-theme");
    const theme = storedTheme === "dark" ? "dark" : "light";
    this.applyTheme(theme);
    this.setState({ theme });
  }

  applyTheme(theme: "light" | "dark") {
    document.documentElement.setAttribute("data-theme", theme);
  }

  handleThemeToggle = () => {
    this.setState(
      (state) => ({
        theme: state.theme === "light" ? "dark" : "light",
      }),
      () => {
        this.applyTheme(this.state.theme);
        localStorage.setItem("owtf-theme", this.state.theme);
      },
    );
  };

  renderRightSide = (links: NavLinkItem[]) => {
    const dropdownLink = links.find((link) => link.dropdown);

    return (
      <div className="flex items-center gap-2">
        {dropdownLink ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="hidden sm:inline-flex">
                {dropdownLink.text}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {(dropdownLink.links || []).map((item) => (
                <DropdownMenuItem key={item.linkTo} asChild>
                  <Link to={item.linkTo}>{item.text}</Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        ) : null}

        <Button
          size="icon"
          variant="outline"
          onClick={this.handleThemeToggle}
          aria-label="Toggle light/dark mode"
        >
          {this.state.theme === "dark" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>

        <div className="md:hidden">
          <MobileNavigationSheet links={links} />
        </div>
      </div>
    );
  };

  render() {
    const links = (this.props.links || []) as NavLinkItem[];
    const navLinks = links.filter((link) => !link.dropdown);

    return (
      <nav className="h-16 border-b border-zinc-200 bg-white/95 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/95">
        <div className="mx-auto flex h-full w-full max-w-[1240px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-6 lg:gap-8">
            <Logo brand={this.props.brand} />
            <DesktopNavMenu links={navLinks} />
          </div>
          {this.renderRightSide(links)}
        </div>
      </nav>
    );
  }
}
