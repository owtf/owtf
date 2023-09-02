/*
 * Component to show if page not found.
 */
import React from 'react';
import { FaRobot } from 'react-icons/fa';
import {Link} from "react-router-dom";


export default class NotFoundPage extends React.Component {
  render() {
    return (
      <section className='notFoundPage'>

        <div className="notFoundPage__contentWrapper">

          <div className='notFoundPage__contentWrapper__headingAndImageContainer'>
            <FaRobot />
            <h2>404</h2>
          </div>

          <div className='notFoundPage__contentWrapper__errorInfoContainer'>
            <h3>Page Not Found!</h3>
            <p>We are unable to find the page you're looking for.</p>
          </div>

          <div className='notFoundPage__contentWrapper__buttonContainer'>
            <Link to="/">Back to Home Page</Link>
          </div>

        </div>
      </section>
    );
  }
}
