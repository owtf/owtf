/*
 * WelcomePage
 */
import React from "react";
import { Link } from "react-router-dom";
const logo = "/img/logo.png";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";

export class WelcomePage extends React.Component {
  // Since state and props are static,
  // there's no need to re-render this component
  shouldComponentUpdate() {
    return false;
  }

  render() {
    return (
      <div className="mx-auto w-full max-w-[1240px] px-4 py-6">
        <Card className="overflow-hidden border-zinc-200 bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-700 p-6 shadow-xl md:p-10">
          <div className="grid items-center gap-8 md:grid-cols-[1.1fr,0.9fr]">
            <div className="space-y-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-300">
                OWASP Security Platform
              </p>
              <h1 className="max-w-[16ch] text-5xl font-semibold leading-[1.02] tracking-tight text-zinc-100 md:text-6xl">
                Offensive Web Testing Framework
              </h1>
              <p className="max-w-[42ch] text-base leading-7 text-zinc-300 md:text-lg">
                OWTF helps security teams automate reconnaissance, validate findings,
                and run repeatable web assessments with less operational friction.
              </p>

              <Button asChild className="h-11 px-6 text-base">
                <Link to="/dashboard">Open Dashboard</Link>
              </Button>
            </div>

            <div className="flex justify-center md:justify-end">
              <img
                src={logo}
                alt="brand logo"
                className="h-56 w-56 rounded-full object-cover opacity-90 shadow-2xl md:h-72 md:w-72"
              />
            </div>
          </div>
        </Card>
      </div>
    );
  }
}
export default WelcomePage;
