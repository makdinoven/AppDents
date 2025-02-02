import { ActionIcon, Tooltip } from '@mantine/core';
import { modals } from '@mantine/modals';
import FeedbackFormModal from 'components/FeedbackFormModal';
import { ModalId } from 'types';
import modalClasses from 'components/Modal/index.module.css';
import Icon, { IconType } from 'components/Icon';

const FeedbackButton = () => (
  <Tooltip
    withArrow
    label="Can't find the course you need? Fill out the form and we'll help you."
    position="top"
    arrowSize={15}
    multiline
  >
    <ActionIcon
      w={65}
      h={65}
      pos="fixed"
      bottom={20}
      style={{ zIndex: 100 }}
      radius="100%"
      variant="filled"
      onClick={() => {
        modals.closeAll();
        modals.open({
          modalId: ModalId.FEEDBACK_FORM,
          children: <FeedbackFormModal onClose={() => modals.close(ModalId.FEEDBACK_FORM)} />,
          size: 'xl',
          withCloseButton: false,
          classNames: {
            header: modalClasses.header,
            content: modalClasses.content,
            body: modalClasses.body,
            root: modalClasses.root,
          },
          yOffset: 41,
          overlayProps: {
            backgroundOpacity: 0.55,
            blur: 3,
          },
        });
      }}
    >
      <Icon type={IconType.Dialog} size={30} color="inherit" />
    </ActionIcon>
  </Tooltip>
);

export default FeedbackButton;
