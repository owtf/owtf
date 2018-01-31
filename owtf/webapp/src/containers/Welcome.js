import React from 'react';
import { push } from 'react-router-redux';
import { Link } from 'react-router';
import styled from 'styled-components';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';


export default class Welcome extends React.Component {
    render() {
        return (
        <WelcomeWrapper>
            <Header>
            <Container>
                <Nav>
                    <Link to="/login">Login</Link>
                </Nav>
            </Container>
            </Header>
            <Hero>
                <Container>
                    <p>Zeus is a dashboard for your change control process.</p>
                </Container>
            </Hero>
            <Body>
                <Container>
                    <Section>
                        <h3>Setup is Easy</h3>
                    </Section>
                </Container>
            </Body>
            <Footer>
            <Container>
                <a
                href="https://github.com/owtf/owtf"
                style={{color: 'inherit', fontWeight: 500}}>
                Zeus
                </a>{' '}
                is Open Source Software
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
  padding: 40px 0;
  background: #7b6be6;
  color: #fff;
`;

const Nav = styled.div `
  float: right;
  a {
    color: #fff;
    &:active,
    &:focus,
    &:hover {
      color: #fff;
    }
  }
`;

const Hero = styled.div `
  margin-bottom: 40px;
  padding: 20px;
  background: #7b6be6;
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
  padding: 20px 0;
`;