import React from 'react';
import { Link } from 'react-router';

import NotFoundError from '../../components/NotFoundError';
import './index.scss'

export default class NotFound extends React.Component {
    render() {
        return (
            <NotFoundError/>
        );
    }
}
