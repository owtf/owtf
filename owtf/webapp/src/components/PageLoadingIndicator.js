import React, {Component} from 'react';

import './PageLoadingIndicator.css';

export default class PageLoadingIndicator extends Component {
  render() {
    let points = 50;
    let duration = 1; // seconds
    let durationPerBit = duration / points;
    let bitWidth = 100 / points;
    let height = 4;
    return (
      <div
        style={{
          display: 'block',
          height: height,
          position: 'fixed',
          width: '100%',
          left: 0,
          right: 0,
          top: 0
        }}>
        {[...Array(points)].map((_, i) => {
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                borderRadius: 0,
                background: '#fff',
                height: height,
                opacity: 0,
                position: 'absolute',
                left: `${bitWidth * i}%`,
                width: `${bitWidth}%`,
                animationDelay: `${durationPerBit * (i + 1)}s`,
                animationName: 'pageLoadingAnim',
                animationDuration: `${duration}s`,
                animationIterationCount: 'infinite',
                animationTimingFunction: 'ease'
              }}
            />
          );
        })}
      </div>
    );
  }
}