/*
 * HomePage
 *
 * This is the first thing users see of our App, at the '/' route
 *
 * NOTE: while this component should technically be a stateless functional
 * component (SFC), hot reloading does not currently support SFCs. If hot
 * reloading is not a necessity for you then you can refactor it and remove
 * the linting exception.
 */

import React from 'react';
import { Container, Message, Button, Header } from 'semantic-ui-react';


export default class HomePage extends React.PureComponent { // eslint-disable-line react/prefer-stateless-function
  render() {
    return (
      <Container>
        <Message>
          <Header as="h1">Offensive Web Testing Framework!</Header>
          <p>
            OWASP OWTF is a project that aims to make security assessments as efficient as possible. Some of the ways in which this is achieved are:
          </p>
          <ul>
            <li>
              Launching a number of tools automatically.
            </li>
            <li>
              Running tests not found in other tools.
            </li>
            <li>
              Providing an interactive interface/report.
            </li>
            <li>
              More info:<a href="https://www.owasp.org/index.php/OWASP_OWTF"> https://www.owasp.org/index.php/OWASP_OWTF </a>
            </li>
          </ul>
          <Button color="blue" href="https://www.owasp.org/index.php/OWASP_OWTF">Learn more</Button>
        </Message>
      </Container>
    );
  }
}
