import React from 'react';
import { shallow } from 'enzyme';
import HelpPage from './index';
import '../../setupTests';
import toJson from 'enzyme-to-json';
import { findByTestAtrr } from '../../utils/testUtils';

const setUp = (props={}) => {
    const wrapper = shallow(<HelpPage {...props} />);
    return wrapper;
};

describe('HelpPage component', () => {

    let wrapper;
    beforeEach(() => {
      wrapper = setUp();
    });

    it('Should render without errors', () => {
        const component = findByTestAtrr(wrapper, "helpComponent");
        expect(component.length).toBe(1);
        expect(toJson(wrapper)).toMatchSnapshot();
    });

    it('Should successfully render sub-components', () => {
        const component = findByTestAtrr(wrapper, "helpBox");
        expect(component.length).toBe(5);
    })

});
