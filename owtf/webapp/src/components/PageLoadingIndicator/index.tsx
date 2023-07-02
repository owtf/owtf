/**
 * Component to show when a page is loading.
 */
import React, { Component } from 'react';

import './index.css';

export default class PageLoadingIndicator extends Component {
  render() {
    const points = 50;
    const duration = 1; // seconds
    const durationPerBit = duration / points;
    const bitWidth = 100 / points;
    const height = 4;
    return (
      <div
        style={{
          display: 'block',
          height,
          position: 'fixed',
          width: '100%',
          left: 0,
          right: 0,
          top: 0,
        }}
      >
        {[...Array(points)].map((_, i) => (
          <span
            key={i}
            style={{
                display: 'inline-block',
                borderRadius: 0,
                background: '#fff',
                height,
                opacity: 0,
                position: 'absolute',
                left: `${bitWidth * i}%`,
                width: `${bitWidth}%`,
                animationDelay: `${durationPerBit * (i + 1)}s`,
                animationName: 'pageLoadingAnim',
                animationDuration: `${duration}s`,
                animationIterationCount: 'infinite',
                animationTimingFunction: 'ease',
              }}
          />
          ))}
      </div>
    );
  }
}
