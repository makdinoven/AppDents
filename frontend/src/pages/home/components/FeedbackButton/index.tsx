import FeedbackFormModal from 'components/FeedbackFormModal';
import Icon, { IconType } from 'components/Icon';
import Popover from 'components/Popover';

const FeedbackButton = () => (
  <Popover
    tooltip={"Can't find the course you need? Fill out the form and we'll help you."}
    buttonProps={{ w: 65, h: 65, pos: 'fixed', bottom: 20, style: { zIndex: 100 }, radius: '100%', variant: 'filled' }}
    target={<Icon type={IconType.Dialog} size={30} color="inherit" />}
    position="top-end"
    floatingSizes={{ h: 83, w: 75, offset: -140 }}
  >
    <FeedbackFormModal />
  </Popover>
);

export default FeedbackButton;
