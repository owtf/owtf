import {css} from 'styled-components';

//github.com/styled-components/styled-components/blob/master/docs/tips-and-tricks.md
const sizes = {
  lg: 1170,
  md: 992,
  sm: 768,
  xs: 376
};

// iterate through the sizes and create a media template
export default Object.keys(sizes).reduce((accumulator, label) => {
  // use em in breakpoints to work properly cross-browser and support users
  // changing their browsers font-size: https://zellwk.com/blog/media-query-units/
  const emSize = sizes[label] / 16;
  accumulator[label] = (...args) => css`
    @media (max-width: ${emSize}em) {
      ${css(...args)}
    }
  `;
  return accumulator;
}, {});