import React from 'react';
import { shallow } from 'enzyme';
import '../../setupTests';
import NavigationBar from './index';
import { findByTestAtrr } from '../../utils/testUtils';
import toJson from 'enzyme-to-json';

const setUp = () => {
  const props = {
    brand: { linkTo: '/', text: 'OWASP OWTF' },
    links: [
      {linkTo: "/dashboard", text: "Dashboard"},
      {linkTo: "/targets", text: "Targets"},
    ]
  };

  const component = shallow(<NavigationBar {...props} />);
  return component;
};

describe('NavigationBar Component', () => {

  let component;
  beforeEach(() => {
    component = setUp();
  });

  it('Should render without errors', () => {
    const wrapper = findByTestAtrr(component, 'navbarTest');
    const tree = toJson(component)
    expect(wrapper.length).toBe(1);
    expect(component.find('Link').length).toBe(1);
    expect(tree).toMatchSnapshot()
  });

  it('Should contain a Link component', () => {
    const tree = toJson(component)
    expect(component.find('Link').length).toBe(1);
    expect(tree).toMatchSnapshot();

  });

  it('Should contain a NavMenu children component', () => {
    const testLinks = [
      {linkTo: "/dashboard", text: "Dashboard"},
      {linkTo: "/targets", text: "Targets"},
    ];
    const tree = toJson(component)
    expect(component.find('NavMenu').length).toBe(1);
    const menuProps = component.find('NavMenu').first().props();
    expect(menuProps.links.length).toEqual(2)
    expect(menuProps.links).toEqual(testLinks)
    expect(tree).toMatchSnapshot();

  });

});

