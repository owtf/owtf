import React from 'react';
import { shallow } from 'enzyme';
import NotFoundPage from './index';
import '../../setupTests';
import toJson from 'enzyme-to-json';

const setUp = (props={}) => {
    const component = shallow(<NotFoundPage {...props} />);
    return component;
};

describe('NotFoundPage Component', () => {

    let component;
    beforeEach(() => {
      component = setUp();
    });

    it('Should render without errors', () => {
      const tree = toJson(component);
      expect(component.find('h3').length).toBe(1);
      expect(component.find('h3').text()).toBe('Page Not Found!');
      expect(tree).toMatchSnapshot();
    });


});
