import React from 'react';
import { push } from 'react-router-redux';
import { Link } from 'react-router';
import styled from 'styled-components';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import Button from '../components/Button';
import {Nav, NavItem} from '../components/Nav';


export default class Welcome extends React.Component {
    render() {
      return (
        <WelcomeWrapper>
            <Header>
            <Container>
                <Nav>
                    <NavItem to="/dashboard">Dashboard</NavItem>
                    <NavItem to="/help">Help</NavItem>
                </Nav>
            </Container>
            </Header>
            <Hero>
                <Container>
                    <h1>Offensive Web Testing Framework!</h1>
                    <p>
                        OWASP OWTF is a project that aims to make security assessments as efficient as possible. Some of the ways in which this is achieved are:
                    </p>
                    <Button type="light" href="http://owtf.org">Learn more</Button>
                </Container>
            </Hero>
            <Body>
                <Container>
                    <Section>
                      <ul>
                          <li>Separating the tests that require no permission from the ones that require permission (i.e. active/ bruteforce).</li>
                          <li>Launching a number of tools automatically.</li>
                          <li>Running tests not found in other tools.</li>
                          <li>Providing an interactive interface/report.</li>
                          <li>More info:
                              <a href="https://www.owasp.org/index.php/OWASP_OWTF" target="__blank__">https://www.owasp.org/index.php/OWASP_OWTF</a>
                          </li>
                      </ul>
                    </Section>
                </Container>
            </Body>
            <Footer>
            <Container>
                <a
                href="https://github.com/owtf/owtf"
                style={{color: 'inherit', fontWeight: 500}}>
                OWTF
                </a>{' '}
                is a flagship OWASP project
            </Container>
            </Footer>
        </WelcomeWrapper>
      );
    }
}

const WelcomeWrapper = styled.div `
  font-size: 18px;
`;

const Container = styled.div `
  max-width: 1000px;
  margin: 0 auto;
`;

const Header = styled.div `
  padding: 60px 0;
  background: #343a40!important;
  color: #fff;
`;

const Hero = styled.div `
  margin-bottom: 40px;
  padding: 20px;
  background: #343a40!important;
  color: #fff;
  text-align: center;
`;

const HeroImage = styled.div `
  margin: 0 auto 20px;
`;

const Body = styled.div `
  margin-bottom: 40px;
`;

const Section = styled.div `
  margin-bottom: 40px;
  > ol > li {
    margin-bottom: 20px;
  }
`;

const GetStarted = styled.div `
  border: 4px solid #111;
  text-align: center;
  padding: 20px;
`;

const Footer = styled.div `
  text-align: center;
  color: #333;
  font-size: 0.8em;
  padding: 10px 0;
`;