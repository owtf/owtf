import React from 'react';
import { push } from 'react-router-redux';
import { Link } from 'react-router';
import styled from 'styled-components';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import Button from '../../components/Button';


export default class Welcome extends React.Component {
    render() {
        return (
           <div>
                <div className="container">
                <div className="jumbotron">
                    <h1>Offensive Web Testing Framework!</h1>
                    <p> OWASP OWTF is a project that aims to make security assessments as efficient as possible. </p>
                    <div className="row" style={{display: 'flex', justifyContent: 'center'}}>
                        <Button type="primary" href="/login">Login</Button>
                    </div>
                </div>
                </div>
            </div>
        );
    }
}