/*
 * Component to show if page not found.
 */
import React from "react";
import { FaRobot } from "react-icons/fa";
import { Link } from "react-router-dom";
import { Button } from "../ui/button";
import { Card } from "../ui/card";


export default class NotFoundPage extends React.Component {
  render() {
    return (
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-[1240px] items-center justify-center px-4 py-8">
        <Card className="w-full max-w-md border-zinc-200 bg-white/95 p-8 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900/85">
          <div className="mb-5 flex items-center justify-center gap-4 text-zinc-900 dark:text-zinc-100">
            <FaRobot className="h-12 w-12" />
            <h2 className="text-7xl font-semibold tracking-tight">404</h2>
          </div>

          <h3 className="mb-3 text-3xl font-semibold tracking-tight">Page Not Found</h3>
          <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-300">
            We are unable to find the page you&apos;re looking for.
          </p>

          <Button asChild>
            <Link to="/">Back to Home Page</Link>
          </Button>
        </Card>
      </section>
    );
  }
}
